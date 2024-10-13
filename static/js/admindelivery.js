function showAddPersonnelForm() {
    document.getElementById('adddeliverypersonneloverlay').style.display = 'flex';
}
function closeAddPersonnelForm() {
    document.getElementById('adddeliverypersonneloverlay').style.display = 'none';
}
document.addEventListener('DOMContentLoaded', (event) => {
    document.getElementById('addpersonnelform').addEventListener('submit', function(event) {
        event.preventDefault(); 
        document.getElementById('nameError').textContent = '';
        document.getElementById('phoneError').textContent = '';
        document.getElementById('emailError').textContent = '';
        const name = document.getElementById('personnelname').value;
        const phone = document.getElementById('personnelphonenumber').value;
        const email = document.getElementById('personnelemail').value;
        let isValid = true;
    
        if (!/^[a-zA-Z\s.]+$/.test(name)) {
        document.getElementById('nameError').textContent = 'Invalid Name.';
        isValid = false;
        }
    
        if (!/^(?:(?:\+|0{0,2})91(\s*[\-]\s*)?|[0]?)?[6789]\d{9}$/.test(phone)) {
            document.getElementById('phoneError').textContent = 'Invalid Phone Number.';
            isValid = false;
        }
    
        if (!/\S+@\S+\.\S+/.test(email)) { 
        document.getElementById('emailError').textContent = 'Invalid Email.';
        isValid = false;
        }
    
        if (isValid) {
            const form = event.target;
            const formData = new FormData(form);
    
            fetch('/adminaddpersonnel/', { 
                method: form.method,
                headers: {
                'X-CSRFToken': getCookie('csrftoken') 
                },
                body: formData 
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                document.getElementById('displaymessage').textContent = 'Delivery personnel added successfully!';
                document.getElementById('success-overlay').style.display = 'flex';
                closeAddPersonnelForm();
                form.reset(); 
                getDeliveryPersonnels();
                } else {
                document.getElementById('displaymessage').textContent = 'Failed to add personnel: ' + data.error;
                document.getElementById('success-overlay').style.display = 'flex';
                closeAddPersonnelForm();
                getDeliveryPersonnels();
                }
            })
            .catch(error => {
                console.error('Error adding personnel:', error);
                document.getElementById('displaymessage').textContent = 'Error adding personnel. Please try again later.';
                document.getElementById('success-overlay').style.display = 'flex';
                closeAddPersonnelForm();
            });
        }
    });
    document.getElementById('confirmMessage').addEventListener('click', () => {
        document.getElementById('success-overlay').style.display = 'none';
    });
});
function getDeliveryPersonnels() {
    fetch('/admingetdeliverypersonnels/', {
      method: 'GET',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        const deliveryPersonalsContainer = document.querySelector('.deliveryPersonal');
        deliveryPersonalsContainer.innerHTML = ''; 
  
        data.data.forEach(personnel => {
            const personnelDiv = document.createElement('div');
            personnelDiv.classList.add('personnel-item');
  
            personnelDiv.innerHTML = `
              <div class="personnel-content">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div class="personnel-image">
                    ${personnel.profile_picture 
                        ? `<img src="${personnel.profile_picture}" alt="Profile Picture">` 
                        : `<img src="/static/images/failed.jpg" alt="Default Profile Picture">`
                    }
                    </div>
                     <div class="personnel-details" id="personnel-details-${personnel.phone_number}"> 
                     <h3>${personnel.first_name}</h3>
                    <p id="phone-${personnel.phone_number}">Phone: ${personnel.phone_number}</p>
                    <p id="email-${personnel.phone_number}">Email: ${personnel.email}</p> 
                    <p>Date Joined: ${personnel.date_joined}</p>
                    </div>
                </div>
                <div class="personnel-actions" id="personnel-actions-${personnel.phone_number}">
                  <button onclick="editDeliveryPersonnel('${personnel.phone_number}','${personnel.first_name}','${personnel.date_joined}')" class="editbtn">
                   <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
                    <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                    <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5z"/>
                    </svg> Edit
                  </button>
                  <button onclick="deleteDeliveryPersonnel('${personnel.phone_number}')" class="deletebtn">
                    <svg style="margin-right: 3px;" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" class="h-5 w-5 shrink-0">
                         <path fill="currentColor" fill-rule="evenodd" d="M10.556 4a1 1 0 0 0-.97.751l-.292 1.14h5.421l-.293-1.14A1 1 0 0 0 13.453 4zm6.224 1.892-.421-1.639A3 3 0 0 0 13.453 2h-2.897A3 3 0 0 0 7.65 4.253l-.421 1.639H4a1 1 0 1 0 0 2h.1l1.215 11.425A3 3 0 0 0 8.3 22H15.7a3 3 0 0 0 2.984-2.683l1.214-11.425H20a1 1 0 1 0 0-2zm1.108 2H6.112l1.192 11.214A1 1 0 0 0 8.3 20H15.7a1 1 0 0 0 .995-.894zM10 10a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0v-5a1 1 0 0 1 1-1m4 0a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0v-5a1 1 0 0 1 1-1" clip-rule="evenodd"></path>
                    </svg>
                    Delete
                  </button>
                </div>
              </div>
            `;
  
          deliveryPersonalsContainer.appendChild(personnelDiv); 
        });
      } else {
        console.error('Error fetching delivery personnels:', data.error);
        document.getElementById('displaymessage').textContent = 'Error fetching personnel: ' + data.error;
        document.getElementById('success-overlay').style.display = 'flex';
      }
    })
    .catch(error => {
      console.error('Error fetching delivery personnels:', error);
      document.getElementById('displaymessage').textContent = 'Error fetching personnel. Please try again later.';
      document.getElementById('success-overlay').style.display = 'flex';
    });
}
function deleteDeliveryPersonnel(phoneNumber){
    document.getElementById('delete-overlay').style.display = 'flex'; 
    const confirmDeleteButton = document.getElementById('confirmDelete');
    confirmDeleteButton.onclick = function() { 
        fetch('/deletedeliverypersonnel/',{
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body:JSON.stringify({phone_number:phoneNumber})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('displaymessage').textContent = 'Delivery personnel deleted successfully!';
                document.getElementById('success-overlay').style.display = 'flex';
                getDeliveryPersonnels();
                document.getElementById('delete-overlay').style.display = 'none';
            } else {
                console.error('Error adding personnel:', data.error);
                document.getElementById('displaymessage').textContent = 'Failed to delete personnel: ' + data.error;
                document.getElementById('success-overlay').style.display = 'flex';
                document.getElementById('delete-overlay').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error deleting personnel:', error);
            document.getElementById('displaymessage').textContent = 'Error deleting personnel. Please try again later.';
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
    getDeliveryPersonnels();
});
function editDeliveryPersonnel(phoneNumber,Name,Datejoined) {
    const detailsDiv = document.getElementById(`personnel-details-${phoneNumber}`);
    const actionsDiv = document.getElementById(`personnel-actions-${phoneNumber}`); 
    const currentPhone = document.getElementById(`phone-${phoneNumber}`).textContent.split(': ')[1]; 
    const currentEmail = document.getElementById(`email-${phoneNumber}`).textContent.split(': ')[1]; 
    detailsDiv.innerHTML = ` 
        <h3>${Name}</h3> 
        <input type="tel" id="edit-phone-${phoneNumber}" value="${currentPhone}" class="edit-input">
        <span class="error-message" id="edit-phone-error-${phoneNumber}"></span> 
        <input type="email" id="edit-email-${phoneNumber}" value="${currentEmail}">
        <span class="error-message" id="edit-email-error-${phoneNumber}"></span>
    `;
    actionsDiv.innerHTML = `
        <button onclick="updateDeliveryPersonnel('${phoneNumber}')" class="updatebtn"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-arrow-up" viewBox="0 0 16 16">
        <path d="M8 11a.5.5 0 0 0 .5-.5V6.707l1.146 1.147a.5.5 0 0 0 .708-.708l-2-2a.5.5 0 0 0-.708 0l-2 2a.5.5 0 1 0 .708.708L7.5 6.707V10.5a.5.5 0 0 0 .5.5"/>
        <path d="M4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm0 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1"/>
        </svg>Update</button>
        <button onclick="cancelEditDeliveryPersonnel('${Name}','${phoneNumber}', '${currentPhone}', '${currentEmail}','${Datejoined}')" class="cancelbtn"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle" viewBox="0 0 16 16">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
        </svg>Cancel</button>
    `;
}

function cancelEditDeliveryPersonnel(Name,phoneNumber, currentPhone, currentEmail,Datejoined) {
    getDeliveryPersonnels();
}

function updateDeliveryPersonnel(phoneNumber) {
    const newPhone = document.getElementById(`edit-phone-${phoneNumber}`).value;
    const newEmail = document.getElementById(`edit-email-${phoneNumber}`).value;
    let isValid = true;
    if (!/^(?:(?:\+|0{0,2})91(\s*[\-]\s*)?|[0]?)?[6789]\d{9}$/.test(newPhone)) {
        document.getElementById(`edit-phone-error-${phoneNumber}`).textContent = 'Invalid Phone Number.';
        isValid = false;
    }
    if (!/\S+@\S+\.\S+/.test(newEmail)) { 
        document.getElementById(`edit-email-error-${phoneNumber}`).textContent = 'Invalid Email.';
        isValid = false;
    }
  
  if (isValid) {
    fetch(/updatedeliverypersonnel/, { 
      method: 'PUT',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify({ 
        phone_number: newPhone, 
        email: newEmail,
        old_number:phoneNumber
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
            document.getElementById('displaymessage').textContent = 'Updated successfully!';
            document.getElementById('success-overlay').style.display = 'flex';
            getDeliveryPersonnels();
      } else {
        console.error('Error updating delivery personnels:', data.error);
        document.getElementById('displaymessage').textContent = 'Error updating personnel: ' + data.error;
        document.getElementById('success-overlay').style.display = 'flex';
      }
    })
    .catch(error => {
        console.error('Error updating delivery personnels:', error);
        document.getElementById('displaymessage').textContent = 'Error updating personnel. Please try again later.';
        document.getElementById('success-overlay').style.display = 'flex';
    });
  }
document.getElementById('confirmMessage').addEventListener('click', () => {
    document.getElementById('success-overlay').style.display = 'none';
});
}
