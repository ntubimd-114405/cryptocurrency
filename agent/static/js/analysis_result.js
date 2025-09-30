document.addEventListener("DOMContentLoaded", function () {
      const backBtn = document.getElementById("back-button");
      const page = document.getElementById("page-content");

      backBtn.addEventListener("click", function (e) {
        e.preventDefault();
        page.classList.remove("fade-in");
        page.classList.add("fade-out");
        setTimeout(() => {
          window.location.href = backBtn.href;
        }, 500);
      });
    });