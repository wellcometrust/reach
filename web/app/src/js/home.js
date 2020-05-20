const home = () => {
  const startButton = document.getElementById('start-button');

  startButton.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById('discover-reach').scrollIntoView({behavior: "smooth", block: "start"});
  });
}

export default home;
