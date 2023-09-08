$(document).ready(function() {

    $("#feedback-form").hide();
    $("#messageArea").on("submit", function(event) {
        const date = new Date();
        const hour = date.getHours();
        const minute = date.getMinutes();
        const str_time = hour + ":" + minute;
        var rawText = $("#text").val();

        var userHtml = '<div class="d-flex justify-content-end mb-4"><div class="msg_cotainer_send">' + rawText + '<span class="msg_time_send">' + str_time + '</span></div><div class="img_cont_msg"><img src="https://i.ibb.co/d5b84Xw/Untitled-design.png" class="rounded-circle user_img_msg"></div></div>';

        $("#text").val("");
        $("#messageFormeight").append(userHtml);

        // Send the user message to the server
        $.ajax({
            data: JSON.stringify({ query: rawText }), // Convert to JSON string
            contentType: "application/json", // Specify content type
            type: "POST",
            url: "/query", // Change to the correct URL
        }).done(function(data) {
            var botHtml = '<div class="d-flex justify-content-start mb-4"><div class="msg_cotainer">' + data + '<span class="msg_time">' + str_time + '</span></div></div>';
            $("#messageFormeight").append($.parseHTML(botHtml));
                    $("#feedback-form").show();
        }).fail(function() {
            // Handle failure here
            console.log("Error sending message to server");
        });

        event.preventDefault();
    });
        
        // Show the feedback form when the thumbs up or thumbs down button is clicked
        $("#messageFormeight").on("click", ".thumbs-button", function() {
            $("#feedback-form").show();
            $("#thumbs-up, #thumbs-down").removeClass("selected");
            $(this).addClass("selected");
        });

        // Handle sending feedback when thumbs up or thumbs down is clicked
        $("#thumbs-up, #thumbs-down").click(function() {
            var isPositive = $(this).attr("id") === "thumbs-up";
            var feedback = isPositive ? "increment" : "decrement";
            
            // Send the feedback to the server using AJAX
            $.ajax({
                type: "POST",
                url: "/feedback",
                contentType: "application/json",  // Add this line
                data: JSON.stringify({ feedback: feedback }),
                success: function(response) {
                    console.log("Feedback sent:", feedback);
                },
                error: function(xhr, status, error) {
                    console.error("Error sending feedback:", error);
                }
            });

            $("#feedback-form").hide();
        });
});
