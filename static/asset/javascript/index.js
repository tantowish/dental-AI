$(document).ready(function(event) { 
    // Tidak bisa submit by enter
    $('#userForm').submit(function(event) {
        event.preventDefault();
        return false; 
    });

    // Deklarasi variabel
    const chatContainer = $("#chat-container");
    const ic3D = $("#ic3D");
    const nama = $("#name");
    const umur = $("#umur");
    const kelamin = $("#kelamin");

    // close dan open chat toggle
    const openChatButton = $("#open-chat");

    let isChatboxOpen = true; 

    let responseCount = 0
    let openChat = false
    let userInfo
    function toggleChatbox(event) {
        event.preventDefault(); 
        if (nama.val().trim() !== "" && umur.val().trim() !== "" && kelamin.val() !== "pilih") {
            $('#error').addClass('hidden')
            chatContainer.toggleClass("hidden");
            ic3D.toggleClass("hidden");
            isChatboxOpen = !isChatboxOpen; // Toggle the state
            userInfo = "Nama saya adalah " + nama.val().trim() + ", Saya berumur " + umur.val().trim() + " Tahun, dan Saya berjenis kelamin " + (kelamin.val() === "L" ? "Laki-laki" : "Perempuan");
            console.log(userInfo)
            return true
        }
        else{
            $('#error').removeClass('hidden')
            return false
        }
    }

    const chat = $('#chat')
    const tm = $('#tm')
    const tmButton = $("#tm-menu")

    let isUpload = false
    tmButton.click(function(event){
        if(isUpload){
            $('#upload-container').toggleClass('hidden')
            chat.toggleClass('hidden')
        }
        else{
            event.preventDefault()
            chat.toggleClass("hidden")
            tm.toggleClass("hidden")
        }
        $('#icTM').toggleClass("hidden")
        $('#icChat').toggleClass("hidden")
    })

    const gigiButton = $("#gigi");

    let clicked
    gigiButton.click(function (event) {
        clicked = "gigi"
        event.preventDefault();
        uploadTemplateShow()
    });

    const gusiButton = $("#gusi");
    gusiButton.click(function (event) {
        clicked = "gusi"
        event.preventDefault();
        uploadTemplateShow()
    });

    const jllButton = $('#jll')
    jllButton.click(function (event) {
        clicked = "jaringan lunak pada mulut"
        event.preventDefault();
        uploadTemplateShow()
    });


    function uploadTemplateShow() {
        console.log(clicked)
        isUpload = true;
        tm.addClass('hidden');
        const uploadTemplateContent = $("#upload").html();
        $('#chat-bg').append(uploadTemplateContent);

        // Call previewImage function when the file input changes
        $('#gambar').on('change', function () {
            previewImage(this);
        });

        $('#kembali-pilih').click(function(event){
            console.log('Masuk')
            tm.removeClass('hidden')
            $('#upload-container').remove()
            isUpload=false
        })

        classifyClick();
    }

    function previewImage(input) {
        const preview = $('#preview');
        const imagePreviewContainer = $('#image-preview');        
        $('#button-classify').removeClass('hidden')


        // Check if a file is selected
        if (input.files && input.files[0]) {
            const reader = new FileReader();

            reader.onload = function (e) {
                // Set the source of the image preview
                preview.attr('src', e.target.result);
            };

            // Read the selected image as a data URL
            reader.readAsDataURL(input.files[0]);

            // Show the image preview container
            imagePreviewContainer.removeClass('hidden');
        } else {
            // If no file is selected, hide the image preview container
            imagePreviewContainer.addClass('hidden');
        }
    }

    openChatButton.click(function(event){
        let isInput = toggleChatbox(event)
        if(!openChat && isInput){
            openChat = true
            $.ajax({
                url: '/intro',
                type: 'POST',
                data: {userInfo: userInfo},
                dataType: 'json',
                success: function(data) {
                    console.log(data.data);
                    // Handle the summary data as needed
                },
                error: function(error) {
                    console.error('Error summarizing:', error);
                }
            });
        }
    });


    $('#appointment').click(function(event){
        // toggleChatbox(event)
        event.preventDefault
        
        if(responseCount>2){
            $('body').append($('#loading-overlay').html());

            $.ajax({
                url: '/summarize',
                type: 'POST',
                data:{
                    nama: nama.val(),
                    umur: umur.val(),
                    jenis_kelamin: kelamin.val()
                },
                dataType: 'json',
                success: function(data) {
                    $('#loading-spinner').addClass('hidden')
                    $('#done-button').removeClass('hidden')

                    $('#result-user').on('click', function() {
                        window.open('/result', '_blank');
                    });

                    const history = data.history

                    $('#daftar').on('click', function() {
                        var newDomainURL = 'https://' + data.link + '/register?rekmed=' + encodeURIComponent(data.rekmed) +
                        '&rangkuman=' + encodeURIComponent(history.rangkuman) +
                        '&rangkumanGambar=' + encodeURIComponent(history.classification) +
                        '&image=' + history.image;
                
                        window.open(newDomainURL, '_blank');
                    });
                },
                error: function(error) {
                    console.error('Error summarizing:', error);
                }
            });
        }
    });

    // Menghindari submit ketika menekan shift
    $('#user-input').keypress(function(event) { 
        if (event.keyCode === 13 && !event.shiftKey) { 
            event.preventDefault(); 
            $('#send-button').click();
        } 
    });

    $('#gambar').on('change', function () {
        previewImage(this);
    });
    

    $('#send-button').click(function (event) {
        event.preventDefault(); 
        var csrftoken = Cookies.get('csrftoken');

        $.ajaxSetup({
            headers: { 'X-CSRFToken': csrftoken }
        });

        var prompt = $('#user-input').val().trim();

        
        if (prompt.trim() !== "") {
            // \n to break
            var formattedPrompt = prompt.replace(/\n/g, '<br>');
            

            // User response
            $('#prompt').append('<div class="mb-2 text-right"><p class="bg-main text-sm text-white rounded-lg py-2 px-4 inline-block">' + formattedPrompt + '</p></div>');
            $('#user-input').val('');

            responseCount++

            // Scroll kebawah chatarea
            var promptHeight = $('#prompt')
            promptHeight.scrollTop(promptHeight.prop("scrollHeight"));

            setTimeout(function () {
                $('#prompt').append('<div id="chat-wait" class="mb-2"><p class="bg-gray-200 text-sm text-gray-700 rounded-lg py-2 px-4 inline-block">...</p></div>');                    
                var promptHeight = $('#prompt')
                promptHeight.scrollTop(promptHeight.prop("scrollHeight"));
            }, 600);
            // Scroll kebawah chat area
            // Bot Response
            $.ajax({
                url: '/',
                type: 'POST',
                data: { prompt: prompt },
                dataType: 'json',
                success: function (data) {
                    // \n to break
                    var formattedResponse = data.response.replace(/\n/g, '<br>');

                    $('#chat-wait').remove();
                    // bubble chat bot
                    $('#prompt').append('<div class="mb-2"><p class="bg-gray-200 text-sm text-gray-700 rounded-lg py-2 px-4 inline-block">' + formattedResponse + '</p></div>');

                    // Scroll kebawah chat area
                    var promptHeight = $('#prompt')
                    promptHeight.scrollTop(promptHeight.prop("scrollHeight"));
                },
                error: function () {
                    // Remove the chat-wait element
                    $('#chat-wait').remove();

                    $('#prompt').append('<div class="mb-2"><p class="bg-gray-200 text-sm text-gray-700 rounded-lg py-2 px-4 inline-block">Error: Terlalu banyak request dalam satu waktu.</p></div>');

                    // Scroll kebawah chat area
                    promptHeight.scrollTop(promptHeight.prop("scrollHeight"));
                }
            });
        }
    });

    function classifyClick() {
        $('#button-classify').click(function (event) {
            console.log('clicked')
            event.preventDefault();
            var fileInput = $('#gambar')[0];
            var file = fileInput.files[0];

            if (file) {
                console.log('masuk file');
                // Create a FormData object to send the file data
                var formData = new FormData();
                formData.append('gambar', file);
                formData.append('clicked', clicked);

                $('#container-upload').toggleClass('hidden');
                $('#waiting').toggleClass('hidden');

                $.ajax({
                    type: 'POST',
                    url: '/classify', // Change this to your actual endpoint
                    data: formData,
                    contentType: false,
                    processData: false,
                    success: function (response) {
                        if(response.classifiedImageUrl){
                            // Handle the success response
                            console.log('File uploaded and classified:');
    
                            // console.log(response.classifiedImageUrl)
                            // $('#text').text(response.classification);
    
                            $('#text').text('Berhasil Upload')
                            $('#loading').addClass('hidden')
    
                            // Display the classified image
                            $('#classified-image').attr('src', response.classifiedImageUrl);
                            $('#classified-image-container').removeClass('hidden');
                            $('#text-appointment').removeClass('hidden');
                        }
                        else{
                            $('#text').text(response.error)
                            $('#loading').addClass('hidden')
                            $('#error-file').removeClass('hidden')
                        }
                    },
                    error: function (error) {
                        $('#text').text('Gagal Upload')
                        $('#loading').remove()
                        $('#error-file').removeClass('hidden')
                        // Handle the error response
                        console.error('Error uploading file:', error);
                    },
                });
            } else {
                alert('Please select a file before submitting.');
            }
            $('#kembali-upload').click(function(event){
                event.preventDefault
                $('#text').text('Menunggu Upload')
                if($('#loading')){
                    $('#loading').removeClass('hidden')
                }
                if($('#error-file')){
                    $('#error-file').addClass('hidden')
                }
                $('#text-appointment').addClass('hidden');
                $('#classified-image-container').addClass('hidden');
                $('#container-upload').removeClass('hidden');
                $('#waiting').addClass('hidden')
                console.log('Masuk')
            })
        });
    }

    var userInput = $('#user-input');

    chatContainer.hover(
        function() {
            chatContainer.addClass('scaled');
        },
        function() {
            // Remove the "scaled" class only if #user-input does not have focus
            if (!userInput.is(':focus')) {
                chatContainer.removeClass('scaled');
            }
        }
    );

    userInput.focus(function() {
        // Add the "scaled" class when #user-input is in focus
        chatContainer.addClass('scaled');
    });

    userInput.blur(function() {
        // Remove the "scaled" class when #user-input loses focus
        chatContainer.removeClass('scaled');
    });
});