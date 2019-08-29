importScripts('https://www.gstatic.com/firebasejs/6.3.4/firebase-app.js')
importScripts('https://www.gstatic.com/firebasejs/6.3.4/firebase-messaging.js')

const config = {
    messagingSenderId: '272029473313'
}

firebase.initializeApp(config)

const messaging = firebase.messaging()

messaging.setBackgroundMessageHandler(payload => {
    const title = payload.notification.title
    console.log('payload', payload.notification.icon)
    const options = {
        body: payload.notification.body,
        icon: payload.notification.icon
    }
    return self.registration.showNotification(title, options)
})
