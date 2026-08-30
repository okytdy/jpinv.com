(function () {
  "use strict";

  var quiz = document.getElementById("governance-quiz");
  if (quiz) {
    var score = 0;
    quiz.querySelectorAll(".gov-question").forEach(function (question) {
      question.querySelectorAll(".gov-option").forEach(function (button) {
        button.addEventListener("click", function () {
          if (question.classList.contains("answered")) return;
          question.classList.add("answered");
          question.querySelectorAll(".gov-option").forEach(function (option) {
            option.disabled = true;
            if (option.dataset.option === question.dataset.correct) option.classList.add("correct");
            else if (option === button) option.classList.add("incorrect");
          });
          if (button.dataset.option === question.dataset.correct) {
            score += 1;
            var output = document.getElementById("governance-quiz-score");
            if (output) output.textContent = String(score);
          }
        });
      });
    });
  }

  if (document.querySelector(".mermaid")) {
    import("https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.esm.min.mjs")
      .then(function (module) {
        module.default.initialize({
          startOnLoad: false,
          theme: "neutral",
          securityLevel: "strict",
          fontFamily: "Noto Sans JP, Hiragino Kaku Gothic ProN, sans-serif",
          themeVariables: {
            primaryColor: "#f4eee4",
            primaryTextColor: "#1a2a4a",
            primaryBorderColor: "#9a7838",
            lineColor: "#304466",
            secondaryColor: "#f5f7fa",
            tertiaryColor: "#fafbfc"
          }
        });
        return module.default.run({ querySelector: ".mermaid" });
      })
      .catch(function () {
        document.querySelectorAll(".mermaid").forEach(function (diagram) {
          diagram.setAttribute("data-render-error", "true");
        });
      });
  }
})();
