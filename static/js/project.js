"use strict";

function showRecipeIds(result) {
    console.log(result);
}

function addRecipe(evt) {
    evt.preventDefault();

    var recipeIds = [];
    $(':checkbox:checked').each(function() {
        recipeIds.push($(this).val());
    });

    $.post('/user-recipes', {'recipe_ids': recipeIds}, showRecipeIds);

}

$('#recipes').on('submit', addRecipe);