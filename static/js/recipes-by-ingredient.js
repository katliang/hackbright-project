"use strict";

// Keeps track of recipes with missing ingredients to be added.
function hideCard(results) {
    // show confirmation message
    $('#another-saved-msg').toggleClass('hidden');
    $('#confirm-add').html('Recipe has been saved.');
    var newSelectorString = '[data-card-recipe-id=' + results['recipe_id'] + ']';
    // hide card
    $(newSelectorString).hide();
    // enable button to generate shopping list
    $('#create-list').prop('disabled', false);

    // hide message after 2 seconds
    setTimeout(function() {
        $('#another-saved-msg').toggleClass('hidden');
    }, 2000);

    }

function addRecipeById(evt) {
    var newRecipeId = $(this).data('recipe-id')
    $.post('/add-recipe-id.json', {'recipe_id': newRecipeId}, hideCard);
}

$('.green.button.add-more-recipes').on('click', addRecipeById);
