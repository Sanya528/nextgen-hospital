function scrollServices(direction) {
  const slider = document.getElementById("servicesSlider");

  if (!slider) {
    console.error("Slider not found!");
    return;
  }

  slider.scrollBy({
    left: direction * 300,
    behavior: "smooth"
  });
}
