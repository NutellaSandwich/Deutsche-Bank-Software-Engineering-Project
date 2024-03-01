// Wait for the DOM to be ready
document.addEventListener("DOMContentLoaded", function() {
    // Get all the sliders
    const sliders = document.querySelectorAll(".slider-input");
  
    // Loop through each slider
    sliders.forEach(function(slider) {
      // Get the range input element
      const rangeInput = slider.querySelector("input[type='range']");
  
      // Get the value span element
      const valueSpan = slider.querySelector(".slider-value");
  
      // Set the initial value of the value span
      valueSpan.innerText = rangeInput.value;
  
      // Add an event listener to update the value span as the range input changes
      rangeInput.addEventListener("input", function() {
        valueSpan.innerText = rangeInput.value;
      });
    });
  });

  