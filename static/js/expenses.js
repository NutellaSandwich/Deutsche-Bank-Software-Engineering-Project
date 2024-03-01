$( function() {
    $("#expensesForm").submit( function() {
        let title = $("#expTitle").val();
        let description = $("#expDescription").val();
        let amount = $("#expAmount").val();
        let date = $("#expDate").val();

        let messageBox = $("#messageBox");
        messageBox.empty();

        // username must be between 5 and 15 characters.
        if (title.length == 0){
            flash("Expense title must not be empty.");
            return false;
        }

        // password must be between 8 and 15 characters.
        if (description.length < 10 ){
            flash("Description must be at least 10 characters long.");
            return false;
        }

        if (date.length == 0){
            flash("Ensure date for expenditure has been recorded.");
            return false;
        }

        return true;
    });

    function flash(message) {
        let messageBox = $("#messageBox");

        messageBox.append("<div class=\"flashedMessage\">" + message + "</div>");
    }
});