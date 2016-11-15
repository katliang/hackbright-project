"use strict";

function displayConfirm(results) {
    if (results.result === false) {
        alert("Sorry, you don't have all the ingredients to make this recipe.");
    } else {
        window.location.href="/main";
    }
}

function checkIngredients(evt) {
    $('#cook-recipe').attr('disabled', true);
    var recipeId = $('#cook-recipe').data('recipe-id');

    $.post("/verify_recipe", {data: recipeId}, displayConfirm);
}

$('#cook-recipe').on('click', checkIngredients);