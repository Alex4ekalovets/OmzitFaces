document.addEventListener("DOMContentLoaded", function () {
    let modal = document.getElementById("myModal");


    const photos = document.querySelectorAll(".photo")
    let modalImg = document.getElementById("img01");
    let captionText = document.getElementById("caption");
    photos.forEach(function (c) {
                        // Для каждой фотографии
                        c.onclick = function () {
                            // Слушаем нажатие
                            // Если нажата, то выбирает тот option, который в тексте кнопки.
                            modal.style.display = "block";
                            modalImg.src = c.src;
                            captionText.innerHTML = c.alt;
                        };
                     })

    let span = document.getElementsByClassName("close")[0];

    span.onclick = function() {
      modal.style.display = "none";
    }
})