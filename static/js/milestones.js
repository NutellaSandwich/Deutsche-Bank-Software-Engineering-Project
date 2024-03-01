$( function() {
    $("#milestonesForm").submit( function() {
        let title = $("#milTitle").val();
        let description = $("#milDescription").val();
        let date = $("#milDate").val();

        let messageBox = $("#messageBox");
        messageBox.empty();

        // username must be between 5 and 15 characters.
        if (title.length == 0){
            flash("Milestone title must not be empty.");
            return false;
        }

        // password must be between 8 and 15 characters.
        if (description.length < 10 ){
            flash("Description must be at least 10 characters long.");
            return false;
        }

        if (date.length == 0){
            flash("Ensure date for milestone has been recorded.");
            return false;
        }

        return true;
    });

    function flash(message) {
        let messageBox = $("#messageBox");

        messageBox.append("<div class=\"flashedMessage\">" + message + "</div>");
    }
});