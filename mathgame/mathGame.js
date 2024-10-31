const prompt=require("prompt-sync")();

function randomNum(min,max) {
    return Math.floor(Math.random()* (max - min)) + min;

}
let input=(prompt("Enter 1 for max game and 2 for 3 lives math game"));

let counter=0;

for (let i=0; i<=10; i++) {
    counter = 0;
}



