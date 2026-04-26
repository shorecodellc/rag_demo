<template>
  <q-layout view="lHh Lpr lFf">

    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn flat dense round icon="menu" class="q-mr-sm" @click="drawer = !drawer" />
        <q-toolbar-title class="text-weight-bold">RAG Demo</q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="drawer"
      show-if-above
      :width="230"
      :breakpoint="700"
      bordered
      class="bg-grey-1"
    >
      <q-scroll-area class="fit">
        <div class="q-px-md q-pt-lg q-pb-sm text-overline text-grey-6 text-weight-bold">
          Tools
        </div>

        <q-list padding>
          <q-item
            clickable
            v-ripple
            to="/"
            exact
            active-class="nav-active"
            class="nav-item rounded-borders q-mb-xs"
          >
            <q-item-section avatar>
              <q-icon name="gavel" size="sm" />
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-medium" style="font-size: 15px">
                Criminal Code RAG
              </q-item-label>
              <q-item-label caption>Retrieval-augmented Q&A</q-item-label>
            </q-item-section>
          </q-item>

          <q-item
            clickable
            v-ripple
            to="/codegen"
            active-class="nav-active"
            class="nav-item rounded-borders q-mb-xs"
          >
            <q-item-section avatar>
              <q-icon name="account_tree" size="sm" />
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-medium" style="font-size: 15px">
                LangGraph Generator
              </q-item-label>
              <q-item-label caption>Generate multi-agent pipelines</q-item-label>
            </q-item-section>
          </q-item>

          <q-item
            clickable
            v-ripple
            to="/horse-predictions"
            active-class="nav-active"
            class="nav-item rounded-borders q-mb-xs"
          >
            <q-item-section avatar>
              <q-icon name="emoji_events" size="sm" />
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-medium" style="font-size: 15px">
                Horse Predictions
              </q-item-label>
              <q-item-label caption>LightGBM backtest analytics</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'MainLayout',

  setup () {
    return {
      drawer: ref(false)
    }
  }
})
</script>

<style scoped>
.nav-item {
  margin-left: 8px;
  margin-right: 8px;
}

.nav-active {
  background: rgba(25, 118, 210, 0.12);
  color: #1976d2;
  border-left: 4px solid #1976d2;
  padding-left: 12px;
}

.nav-active .q-icon {
  color: #1976d2;
}
</style>
