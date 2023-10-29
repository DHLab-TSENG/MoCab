<template>
  <p>Authenticating...</p>
</template>

<script>
import FHIR from "fhirclient"
// import {launch} from "@/baseModel/launch_auth"
export default {
  name: 'SmartLaunch',
  async created() {
    FHIR.oauth2.authorize({
      "client_id": "804bbc36-ff36-48e8-842e-2254a2d35a86",
      "scope": "patient/*.read Launch"
    });
    // await launch()
  }

}
</script>

<style scoped>

</style>