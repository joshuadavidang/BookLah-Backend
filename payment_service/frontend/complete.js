document.addEventListener("DOMContentLoaded", async() => {
    const {publishable_key} = await fetch("/config").then (r => r.json())
    const stripe = Stripe(publishable_key)

    const params = new URLSearchParams(window.location.href)
    const client_secret = params.get("payment_intent_client_secret")

    const payment_intent = await stripe.retrievePaymentIntent(client_secret)
    const payment_intent_pre = document.getElementById("payment-intent")
    payment_intent_pre.innerText = JSON.stringify(payment_intent, null, 2)
})