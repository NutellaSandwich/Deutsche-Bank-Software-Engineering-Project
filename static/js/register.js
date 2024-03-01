$( function() {
    $("#registerForm").submit( function() {
        let username = $("#username").val();
        let email = $("#email").val();
        let password = $("#password").val();

        let messageBox = $("#messageBox");
        messageBox.empty();

        // Regex to check if a string contains uppercase, lowercase, special characters & numeric value
        let passwordPattern = new RegExp(
            "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[-+_!@#$%^&*.,?]).+$"
        );

        let emailPattern = new RegExp(
            "[A-Za-z0-9\.]+@[A-Za-z0-9\.]+\.[A-Za-z0-9\.]+"
        );

        // username must be between 5 and 15 characters.
        if (username.length < 5 || username.length > 15){
            flash("Username must be between 5 and 15 characters.");
            console.log(username);
            return false;
        }

        // password must be between 8 and 15 characters.
        if (password.length < 8 || password.length > 15){
            flash("Password must be between 8 and 15 characters");
            return false;
        }

        
        if (!emailPattern.test(email)){
            flash("Please enter a valid email address");
            return false;
        }

        // password must contain at least one digit.
        // password must contain at least one uppercase character
        // password must contain at least one lowercase character
        // password much contain at least one symbol
        if (!passwordPattern.test(password)){
            flash("Password must contain at least one lowercase character, uppercase character, digit and symbol.");
            return false;
        }

        return true;
    });

    function flash(message) {
        let messageBox = $("#messageBox");

        messageBox.append("<div class=\"flashedMessage\">" + message + "</div>");
    }
});
