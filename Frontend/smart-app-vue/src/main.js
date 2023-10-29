import { createApp } from 'vue'
import App from './App.vue'
import {store} from './dataStore'

createApp(App)
    .use(store)
    .mount('#app')
