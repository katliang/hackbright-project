"use strict";

// Keeps track of recipes with missing ingredients to be added.
function showConfirmMsg(results) {
    $('#confirm-add').html('Recipe has been saved. Generate shopping list.');
    $('#create-list').attr('disabled', false);
    
    }

function getIds(evt) {
    evt.preventDefault();
    $('#add-submit-button').attr('disabled', true);
    var recipeIds = [];
    $('input:checkbox:checked').each(function() {
        recipeIds.push($(this).data('recipe-id'));
    })

    $.post("/add-recipe-id.json", {"recipe-ids": recipeIds}, showConfirmMsg);

}

$('#add-recipe').on('submit', getIds);
