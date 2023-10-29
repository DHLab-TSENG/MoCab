import { createApp } from 'vue'
import SmartLaunch from "@/pages/launch/SmartLaunch"
import { store } from '@/dataStore'

createApp(SmartLaunch)
    .use(store)
    .mount('#launch')
