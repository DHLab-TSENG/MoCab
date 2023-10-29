import {createRouter, createWebHistory} from "vue-router"
import SmartLaunch from "./SmartLaunch"
import App from './App'

export const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: "/" , component: App},
        { path: '/launch', component: SmartLaunch },
    ]

})