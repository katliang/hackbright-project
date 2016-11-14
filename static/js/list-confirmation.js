"use strict";

// Changes quantity and unit fields to required if checkbox is checked
// Changes back to not required if checkbox is unchecked
function makeRequired(evt) {
    $(':checkbox:checked').next().prop('required', true);
    $(':checkbox:checked').next().next().prop('required', true);
    }


$('.checkbox').on('change', makeRequired);


function sendToMain(results) {
    window.location.href="/search";
}

function getInventoryInfo(evt) {
    evt.preventDefault();
    var shoppingListId = $('#shopping_list').data('shopping-list-id')
    var inventory = {};
    // if the checkbox is checked:
    $(':checkbox:checked').each(function() {
    // get the values from the next two fields
        var ingredientId = $(this).data('ingredient-id');
        var ingredientName = $(this).data('ingredient-name');
        var ingredientQty = $(this).next().val();
        var ingredientUnit = $(this).next().next().val();
        inventory[ingredientId] = {};
        inventory[ingredientId]['ingredientName'] = ingredientName;
        inventory[ingredientId]['ingredientQty'] = ingredientQty;
        inventory[ingredientId]['ingredientUnit'] = ingredientUnit;
    })

    $.post("/inventory", {data: JSON.stringify(inventory), listId: shoppingListId}, sendToMain)
    }



$('#shopping_list').on('submit', getInventoryInfo);