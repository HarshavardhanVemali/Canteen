/*  Menu scripts   */
function showMenuForm() {
    document.getElementById('addmenuoverlay').style.display = 'flex';
}
function closeMenuForm() {
    document.getElementById('addmenuoverlay').style.display = 'none';
}
document.addEventListener('DOMContentLoaded', (event) => {
    const imageInput = document.getElementById('menuimage');
    const imagePreview = document.getElementById('imagePreview');

    imageInput.addEventListener('change', function(event) {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block'; 
            }
            reader.readAsDataURL(this.files[0]); 
        } else {
            imagePreview.src = '#';
            imagePreview.style.display = 'none'; 
        }
    });
    document.getElementById('addmenuform').addEventListener('submit', function(event) {
        event.preventDefault(); 
        document.getElementById('nameError').textContent = '';
        const name = document.getElementById('menuname').value;
        let isValid = true;
    
        if (!/^[a-zA-Z\s.]+$/.test(name)) {
            document.getElementById('nameError').textContent = 'Invalid Name.';
            isValid = false;
        }
    
        if (isValid) {
            const form = event.target;
            const formData = new FormData(form);
    
            fetch('/adminaddmenu/', { 
                method: form.method,
                headers: {
                'X-CSRFToken': getCookie('csrftoken') 
                },
                body: formData 
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                document.getElementById('displaymessage').textContent = 'Menu created successfully!';
                document.getElementById('success-overlay').style.display = 'flex';
                closeMenuForm();
                getMenu();
                const imagePreview = document.getElementById('imagePreview');
                imagePreview.src = '#';
                imagePreview.style.display = 'none';
                form.reset(); 
                } else {
                document.getElementById('displaymessage').textContent = 'Failed to create menu: ' + data.error;
                document.getElementById('success-overlay').style.display = 'flex';
                getMenu();
                closeMenuForm();
                const imagePreview = document.getElementById('imagePreview');
                imagePreview.src = '#';
                imagePreview.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error adding personnel:', error);
                document.getElementById('displaymessage').textContent = 'Error in creating menu. Please try again later.';
                document.getElementById('success-overlay').style.display = 'flex';
                closeMenuForm();
            });
        }
    });
    document.getElementById('confirmMessage').addEventListener('click', () => {
        document.getElementById('success-overlay').style.display = 'none';
    });
});
function getMenu() {
    fetch('/admingetmenu/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const menuContainer = document.querySelector('.menuitems');
            menuContainer.innerHTML = '';

            data.data.forEach(menu => {
                const menuDiv = document.createElement('div');
                menuDiv.classList.add('menu-items');

                menuDiv.innerHTML = `
                  <div class="menu-item">
                    <div class="image-container">
                      ${menu.menu_picture
                        ? `<img src="${menu.menu_picture}" alt="Menu Image">`
                        : `<img src="static/images/failed_image_2.jpg" alt="Default Image">`
                      }
                      <input type="file" id="changephoto-${menu.menu_id}" style="display: none;" accept="image/*">
                      <label for="changephoto-${menu.menu_id}" class="photo-icon">
                        <img src="/static/images/photoicon.jpg" alt="Change Photo">
                      </label>
                    </div>
                    <h4>${menu.menu_name}</h4>
                    <div class="menu-actions">
                      <button onclick="deleteMenu('${menu.menu_id}')" class="deletebtn">
                        <svg style="margin-right: 3px;" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" class="h-5 w-5 shrink-0">
                            <path fill="currentColor" fill-rule="evenodd" d="M10.556 4a1 1 0 0 0-.97.751l-.292 1.14h5.421l-.293-1.14A1 1 0 0 0 13.453 4zm6.224 1.892-.421-1.639A3 3 0 0 0 13.453 2h-2.897A3 3 0 0 0 7.65 4.253l-.421 1.639H4a1 1 0 1 0 0 2h.1l1.215 11.425A3 3 0 0 0 8.3 22H15.7a3 3 0 0 0 2.984-2.683l1.214-11.425H20a1 1 0 1 0 0-2zm1.108 2H6.112l1.192 11.214A1 1 0 0 0 8.3 20H15.7a1 1 0 0 0 .995-.894zM10 10a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0v-5a1 1 0 0 1 1-1m4 0a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0v-5a1 1 0 0 1 1-1" clip-rule="evenodd"></path>
                        </svg> Delete
                      </button>
                    </div>
                  </div>
                `;

                menuContainer.appendChild(menuDiv);
                const changePhotoInput = document.getElementById(`changephoto-${menu.menu_id}`);
                changePhotoInput.addEventListener('change', function(event) {
                    const menuImage = this.parentNode.querySelector('img');
                    const menuId = this.id.split('-')[1];

                    if (this.files && this.files[0]) {
                        const formData = new FormData();
                        formData.append('menuimage', this.files[0]);
                        formData.append('menu_id',menuId)
                        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

                        fetch(/adminupdatemenu/, {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                document.getElementById('displaymessage').textContent = 'Menu Updated successfully!';
                                document.getElementById('success-overlay').style.display = 'flex';
                                getMenu();
                            } else {
                                document.getElementById('displaymessage').textContent = 'Failed to update menu: ' + data.error;
                                document.getElementById('success-overlay').style.display = 'flex';
                                getMenu();
                            }
                        })
                        .catch(error => {
                            console.error('Error adding personnel:', error);
                            document.getElementById('displaymessage').textContent = 'Error in updating menu. Please try again later.';
                            document.getElementById('success-overlay').style.display = 'flex';
                        });
                    }
                });
            });
        } else {
            console.error('Error fetching menu:', data.error);
            document.getElementById('displaymessage').textContent = 'Error fetching menu: ' + data.error;
            document.getElementById('success-overlay').style.display = 'flex';
        }
    })
    .catch(error => {
        console.error('Error fetching menu:', error);
        document.getElementById('displaymessage').textContent = 'Error fetching menu. Please try again later.';
        document.getElementById('success-overlay').style.display = 'flex';
    });
}
function deleteMenu(menuId){
    document.getElementById('delete-overlay').style.display = 'flex'; 
    const confirmDeleteButton = document.getElementById('confirmDelete');
    confirmDeleteButton.onclick = function() { 
        fetch('/admindeletemenu/',{
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body:JSON.stringify({menu_id:menuId})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('displaymessage').textContent = 'Menu deleted successfully!';
                document.getElementById('success-overlay').style.display = 'flex';
                getMenu();
                document.getElementById('delete-overlay').style.display = 'none';
            } else {
                console.error('Error adding personnel:', data.error);
                document.getElementById('displaymessage').textContent = 'Failed to delete menu: ' + data.error;
                document.getElementById('success-overlay').style.display = 'flex';
                document.getElementById('delete-overlay').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error deleting personnel:', error);
            document.getElementById('displaymessage').textContent = 'Error deleting menu. Please try again later.';
            document.getElementById('success-overlay').style.display = 'flex'; 
        });
    };
    document.getElementById('cancelDelete').onclick = function() { 
        document.getElementById('delete-overlay').style.display = 'none';
    }; 
    document.getElementById('confirmMessage').addEventListener('click', () => {
        document.getElementById('success-overlay').style.display = 'none';
    });   
}
document.addEventListener('DOMContentLoaded', () => {
    getMenu();
});
