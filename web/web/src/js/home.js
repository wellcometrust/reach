const home = () => {
  const startButton = document.getElementById('start-button');

    if (startButton) {
      startButton.addEventListener("click", (e) => {
        e.preventDefault();
        document.getElementById('discover-reach').scrollIntoView({behavior: "smooth", block: "start"});
      });
    }
}

export default home;
