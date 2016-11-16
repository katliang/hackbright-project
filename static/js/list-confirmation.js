"use strict";

// Changes quantity and unit fields to required if checkbox is checked
// Changes back to not required if checkbox is unchecked
function makeRequired(evt) {
    $(':checkbox:checked').next().prop('required', true);
    $(':checkbox:checked').next().next().prop('required', true);
    var defaultQty = $(this).next().data('default-quantity');
    $(this).next().val(defaultQty);
    }

$('.checkbox').on('change', makeRequired);


// Redirect to main page.
function sendToMain(results) {
    window.location.href="/main";
}

// When the form is submitted, iterate through the checked checkboxes.
// For each checked checkbox, get the values from the next two fields.
function getInventoryInfo(evt) {
    evt.preventDefault();
    var shoppingListId = $('#shopping_list').data('shopping-list-id')
    var inventory = {};
    $('input:checkbox:checked').each(function() {
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


// When the button is clicked, all the checkboxes are checked.
function selectAllCheckboxes(evt) {
    $('input:checkbox').each(function() {
        $(this).prop('checked', true);
        var defaultQty = $(this).next().data('default-quantity');
        $(this).next().val(defaultQty);
    })
}

$('#select-all').on('click', selectAllCheckboxes);
