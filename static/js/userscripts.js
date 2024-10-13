function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
        }
    }
    }
    return cookieValue;
}

const cartitemsSocket = new WebSocket('ws://127.0.0.1:8000/ws/cartitems/');
const allitemsDiv = document.querySelector('.order-items'); 

cartitemsSocket.onopen = function(event) {
    console.log('Connected to All Items WebSocket server!');
};
let totalAmount = 0; 
cartitemsSocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.data) {
        if(data.data.length>0){
            document.querySelector('.checkout-page').style.display='flex';
            document.getElementById('emptycart').style.display='none';
            allitemsDiv.innerHTML = '';
            totalAmount=0;
            let totalCount = 0;
            data.data.forEach(item => {
                const itemHtml = `
                    <div class="order-item">
                        <img src="${item.item_image}" alt="${item.item_name}" class="item-image" />
                        <div>
                            <div class="item-header">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="${item.type === 'non_veg' ? 'rgb(239, 79, 95)' : 'rgb(27, 166, 114)'}" stroke-width="2" class="bi bi-caret-up-square ${item.type === 'non_veg' ? 'non-veg' : 'veg'}" viewBox="0 0 16 16">
                                    <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
                                    <path d="M3.544 10.705A.5.5 0 0 0 4 11h8a.5.5 0 0 0 .374-.832l-4-4.5a.5.5 0 0 0-.748 0l-4 4.5a.5.5 0 0 0-.082.537"/>
                                </svg>
                                <h4 class="item-name">${item.item_name}</h4>
                            </div>
                            <p>Delivery Time: ${item.preparation_time} mins</p>
                            <p>${item.description}</p>
                            <div class="item-price">
                                <div class="quantity-control">
                                    <button class="quantity-btn" id="decrease" onclick="updatecart(${item.id},'decrement')" style="display:flex;align-items:center;"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-dash" viewBox="0 0 16 16">
                                    <path d="M4 8a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 8"/>
                                    </svg></button>
                                    <p class="quantity">${item.quantity}</p>
                                    <button class="quantity-btn" id="increase" onclick="updatecart(${item.id},'increment')">+</button>
                                </div>
                                <p class="price" id="itemPrice">₹${(item.price * item.quantity).toFixed(2)}</p>
                            </div>
                        </div>
                    </div>
                `;
                allitemsDiv.innerHTML += itemHtml;
                totalAmount += item.price * item.quantity; 
                totalCount += item.quantity;
            });
            document.getElementById('item-count').innerText = `Total Items: ${totalCount}`; 
        }
        else{
            document.getElementById('emptycart').style.display='flex';
            document.querySelector('.checkout-page').style.display='none';
        }
    } else {
        console.log("No item data received in the message.");
    }
};
function updatecart(itemId, operation) {
    const formData = new FormData();
    formData.append('operation', operation);
    formData.append('item_id',itemId);
    fetch(/updatecartitem/, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken') 
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Cart updated successfully.');
        } else {
            console.error(data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}

const additionalpricesSocket = new WebSocket('ws://127.0.0.1:8000/ws/additionalprices/');

additionalpricesSocket.onopen = function(event) {
    console.log('Connected to AdditionalPrices WebSocket server!');
};

additionalpricesSocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    const billDetailsDiv = document.querySelector('.bill-details');
    billDetailsDiv.innerHTML = `
        <h3>Bill Details</h3>
    `;
    const itemTotalDiv=document.createElement('div');
    itemTotalDiv.classList.add('bill-item');
    itemTotalDiv.innerHTML=`
        <span>Item Total</span>
        <span class="bill-price" id="bill-item-total">₹ ${totalAmount}</span>
    `;
    billDetailsDiv.appendChild(itemTotalDiv);
    let additionalTotal = 0;
    data.data.forEach(price => {
        const charge = price.value_type === 'Percentage' ? (totalAmount * (price.value / 100)) : price.value;
        additionalTotal += charge;
        const billItemDiv = document.createElement('div');
        billItemDiv.classList.add('bill-item'); 
        billItemDiv.innerHTML = `
            <span>${price.price_type}${price.value_type === 'Percentage' ? ` (${price.value}%)` : ''}</span>
            <span class="bill-price">₹ ${charge.toFixed(2)}</span>
        `;
        billDetailsDiv.appendChild(billItemDiv);
    });
    const hr = document.createElement('hr');
    billDetailsDiv.appendChild(hr); 
    const finalAmount = totalAmount + additionalTotal;
    const finalBillItemDiv = document.createElement('div');
    finalBillItemDiv.classList.add('bill-item');
    finalBillItemDiv.innerHTML = `
        <span><strong>To Pay</strong></span>
        <span class="bill-price" id="order-total">₹ ${finalAmount.toFixed(2)}</span>
    `;
    billDetailsDiv.appendChild(finalBillItemDiv);
};
