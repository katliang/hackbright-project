"use strict";

function removeCard(result) {
    // show confirmation message
    $('.ui.success.message').show();
    $('#confirm-add-recipe').html('Recipe has been saved.');
    var selectorString = '[data-card-recipe-id=' + result['recipe_id'] + ']';
    // hide card
    $(selectorString).hide();
    // enable button to generate shopping list
    $('#new-list').prop('disabled', false);

    // hide message after 2 seconds
    setTimeout(function() {
        $('.ui.success.message').hide();
    }, 2000);
}

function addRecipe(evt) {
    // get the id
    var recipeId = $(this).data('recipe-id')
    // send it to the route
    $.post('/user-recipes', {'recipe_id': recipeId}, removeCard);
    // when you come back, hide the card

}

$('.green.button.add-recipe').on('click', addRecipe);