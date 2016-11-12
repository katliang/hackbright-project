"use strict";

function showRecipeIds(result) {
    console.log(result);
}

// Creates a list of ids and sends in a dict to route
function addRecipe(evt) {
    evt.preventDefault();
    $('#submit').attr('disabled', true);
    var recipeIds = [];
    $(':checkbox:checked').each(function() {
        recipeIds.push($(this).val());
    });

    $.post('/user-recipes.json', {'recipe_ids': recipeIds}, showRecipeIds);

}

$('#recipes').on('submit', addRecipe);