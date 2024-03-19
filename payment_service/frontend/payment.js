document.addEventListener("DOMContentLoaded", async() => {
    const {publishable_key} = await fetch("/config").then (r => r.json())
    const stripe = Stripe(publishable_key)

    const {client_secret} = await fetch("/api/v1/processPayment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        }
    }).then (r => r.json())

    console.log("test")
    console.log(client_secret)


    const elements = stripe.elements({clientSecret: client_secret})
    const payment_element = elements.create("payment")
    payment_element.mount("#payment-element")

    const form = document.getElementById("payment-form")
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const error = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: window.location.href.split("?")[0] + "complete.html"
            }
        })
        if (error){
            const message = document.getElementById("error-message")
            message.innerText - error.message;
        }
    })

})