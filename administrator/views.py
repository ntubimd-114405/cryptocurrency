# administrator/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q  

from main.models import Coin

# ✅ 只允許 superuser 進入
from django.contrib.auth.decorators import user_passes_test

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


# ============================
# 後台 Dashboard
# ============================
@superuser_required
def dashboard(request):
    return render(request, 'administrator/dashboard.html')


# ============================
# 幣種管理
# ============================
@superuser_required
def crypto_management(request):
    query = request.GET.get('q', '')  # 預設是空字串，不會出現 None
    coins = Coin.objects.all()

    if query:
        coins = coins.filter(
            Q(coinname__icontains=query) |
            Q(abbreviation__icontains=query)
        )

    return render(request, 'administrator/crypto_management.html', {
        'coins': coins,
        'query': query
    })


@superuser_required
def edit_crypto(request, id):
    coin = get_object_or_404(Coin, id=id)
    
    if request.method == 'POST':
        coin.coinname = request.POST.get('coinname')
        coin.abbreviation = request.POST.get('abbreviation')
        coin.logo_url = request.POST.get('logo_url')
        coin.api_id = request.POST.get('api_id')
        coin.save()
        
        return HttpResponseRedirect(reverse('administrator:crypto_management'))
    
    return render(request, 'administrator/edit_crypto.html', {'coin': coin})


@superuser_required
def delete_crypto(request, id):
    coin = get_object_or_404(Coin, id=id)
    
    if request.method == 'POST':
        coin.delete()
        return redirect('administrator:crypto_management')

    return render(request, 'administrator/delete_crypto_confirm.html', {'coin': coin})


# ============================
# 使用者管理
# ============================
@superuser_required
def user_management(request):
    query = request.GET.get('q', '')  
    users = User.objects.select_related('profile')

    if query:
        users = users.filter(username__icontains=query) | users.filter(email__icontains=query)

    return render(request, 'administrator/user_management.html', {'users': users, 'query': query})


@superuser_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        membership = request.POST.get("membership")
        is_active = request.POST.get("is_active") == "1"
        new_password = request.POST.get("password")

        # 更新基本欄位
        user.username = username
        user.email = email
        user.is_active = is_active

        if new_password:
            user.password = make_password(new_password)

        user.save()

        # 更新 Profile
        user.profile.membership = membership
        user.profile.save()

        return redirect("administrator:user_management")

    return render(request, "administrator/edit_user.html", {"user": user})


from django.shortcuts import render
from report.models import DialogEvaluation  # 替換成你的 app 名稱

def dialog_evaluation_list(request):
    evals = DialogEvaluation.objects.all().order_by('created_at')
    return render(request, 'administrator/dialog_evaluation_list.html', {'evals': evals})



from django import forms
class DialogEvaluationForm(forms.ModelForm):
    class Meta:
        model = DialogEvaluation
        fields = '__all__'
        widgets = {
            'user_input': forms.Textarea(attrs={'rows':3}),
            'expected_response': forms.Textarea(attrs={'rows':3}),
            'generated_response': forms.Textarea(attrs={'rows':5}),
            'analyze_data': forms.Textarea(attrs={'rows':5}),
        }

def dialog_evaluation_detail(request, pk):
    eval_obj = get_object_or_404(DialogEvaluation, pk=pk)

    if request.method == 'POST':
        form = DialogEvaluationForm(request.POST, instance=eval_obj)
        if form.is_valid():
            form.save()
            return redirect('administrator:dialog_evaluation_list')
    else:
        form = DialogEvaluationForm(instance=eval_obj)

    return render(request, 'administrator/dialog_evaluation_detail.html', {'form': form, 'eval_obj': eval_obj})




import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge import Rouge
import jieba

def evaluate_dialogs(request):
    queryset = DialogEvaluation.objects.all().values(
        'expected_intent', 'predicted_intent',
        'expected_response', 'generated_response', 'task_success'
    )
    df = pd.DataFrame(list(queryset))

    if len(df) == 0:
        return render(request, 'administrator/dialog_evaluation_eval.html', {'error': '目前沒有對話資料可供分析。'})

    # 填充 NaN
    df['expected_intent'] = df['expected_intent'].fillna("").astype(str)
    df['expected_response'] = df['expected_response'].fillna("").astype(str)
    df['predicted_intent'] = df['predicted_intent'].fillna("").astype(str)
    df['generated_response'] = df['generated_response'].fillna("").astype(str)

    total_count = len(df)
    filtered_df = df[~df['expected_intent'].str.contains(r'\(人工\)', na=False) &
                     ~df['expected_response'].str.contains(r'\(人工\)', na=False)]
    analyzed_count = len(filtered_df)

    if analyzed_count == 0:
        return render(request, 'administrator/dialog_evaluation_eval.html', {
            'error': '所有對話皆為人工標註，無自動分析資料可供計算。',
            'total_count': total_count,
            'analyzed_count': analyzed_count
        })

    # Intent Accuracy & F1
    intent_acc = accuracy_score(filtered_df['expected_intent'], filtered_df['predicted_intent'])
    intent_f1 = f1_score(filtered_df['expected_intent'], filtered_df['predicted_intent'], average='weighted')

    # BLEU & ROUGE
    bleu_scores, rouge_scores = [], []
    rouge = Rouge()
    smooth_fn = SmoothingFunction().method1

    for _, row in filtered_df.iterrows():
        expected = str(row['expected_response']).strip() or " "
        generated = str(row['generated_response']).strip() or " "

        # BLEU：逐字計算
        ref = [list(expected)]
        hyp = list(generated)
        bleu = sentence_bleu(ref, hyp, smoothing_function=smooth_fn)
        bleu_scores.append(bleu)

        # 中文斷詞後計算 ROUGE-L
        expected_cut = " ".join(jieba.lcut(expected))
        generated_cut = " ".join(jieba.lcut(generated))

        rouge_scores_val = rouge.get_scores(generated_cut, expected_cut)
        rouge_score = rouge_scores_val[0]['rouge-l']['f']
        rouge_scores.append(rouge_score)

    # 平均分數
    avg_bleu = sum(bleu_scores) / len(bleu_scores)
    avg_rouge = sum(rouge_scores) / len(rouge_scores)
    task_success_rate = filtered_df['task_success'].mean()
    overall_score = 0.4 * intent_acc + 0.3 * task_success_rate + 0.3 * avg_bleu

    # 結構化報告
    structured_report = [
        ("Intent Accuracy", f"{intent_acc:.3f}", intent_acc),
        ("Intent F1-score", f"{intent_f1:.3f}", intent_f1),
        ("Avg BLEU Score", f"{avg_bleu:.3f}", avg_bleu),
        ("Avg ROUGE-L Score", f"{avg_rouge:.3f}", avg_rouge),
        ("Task Success Rate", f"{task_success_rate:.3f}", task_success_rate),
        ("Overall Score (Weighted)", f"{overall_score:.3f}", overall_score),
    ]

    # 儲存 CSV
    filtered_df['BLEU'] = bleu_scores
    filtered_df['ROUGE-L'] = rouge_scores
    filtered_df.to_csv("dialog_eval_results.csv", index=False, encoding="utf-8-sig")

    return render(
        request,
        'administrator/dialog_evaluation_eval.html',
        {
            'structured_report': structured_report,
            'total_count': total_count,
            'analyzed_count': analyzed_count
        }
    )