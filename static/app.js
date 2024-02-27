// Search bar input
const input = document.querySelector("#search");

// Suggestions 
const suggestions = document.querySelector(".suggestions ul");

// Array of all movies
const all = [
  "Castle in the Sky",
  "Kiki's Delivery Service",
  "Only Yesterday",
  "Porco Rosso",
  "Pom Poko",
  "Whisper of the Heart",
  "Princess Mononoke",
  "My Neighbors the Yamadas",
  "The Cat Returns",
  "Tales from Earthsea",
  "Ponyo",
  "Arrietty",
  "From Up on Poppy Hill",
  "The Wind Rises",
  "The Tale of the Princess Kaguya",
  "When Marnie Was There",
  "The Red Turtle",
  "Earwig and the Witch",
  "Grave of the Fireflies",
  "Spirited Away",
  "My Neighbor Totoro",
  "Howl's Moving Castle",
];


// putting results in empty array as letters typed
function search(q) {

  q.toLowerCase();

  // Empty array if empty query
  if (q === "") {
    return [];
  }

  // Filtered array   
  let results = all.filter((f) => f.toLowerCase().includes(q));
  return results;
}

//what should happen after each key press, runs showSuggestion
function searchHandler(e) {

  //clearing previous selections
  suggestions.innerHTML = ``;

  //array of possible results
  let sugArr = search(e.target.value);

  //adding each movie as li with class has-suggestions
  for (let i = 0; i < sugArr.length; i++) {
    const sugg = document.createElement("li");
    sugg.classList.add(`has-suggestions`);
    sugg.innerText = sugArr[i];
    suggestions.append(sugg);
  }
}

//making the suggestion the actual input
function useSuggestion(e) {
  input.value = e.target.innerText;
  //clearing previous selections
  suggestions.innerHTML = ``;
}

//everytime key pressed, searchHandler should show suggestions
input.addEventListener("keyup", searchHandler);
suggestions.addEventListener("click", useSuggestion);
