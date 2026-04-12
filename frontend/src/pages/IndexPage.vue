<template>
  <q-page class="q-pa-md flex flex-center">
    <div style="width: 100%; max-width: 800px;">

      <div class="text-h4 q-mb-md">
        ⚖️ Canadian Criminal Code RAG (Retrieval Only)
      </div>
      <div class='text-h6 q-mb-md'>
        This is not to be considered legal advice, contact a lawyer or the police for serious questions about the law
      </div>

      <!-- Form -->
      <q-card class="q-pa-md q-mb-md">
        <q-input
          v-model="apiKey"
          type="password"
          label="OpenAI API Key"
          filled
          class="q-mb-md"
        />

        <q-input
          v-model="query"
          type="textarea"
          label="Enter your legal question"
          filled
          autogrow
          class="q-mb-md"
        />

        <!-- Example Queries -->
        <div class="q-mb-md">
          <div class="text-subtitle2 q-mb-sm text-grey">
            Example queries:
          </div>

          <q-list bordered separator>
            <q-item clickable v-ripple @click="setQuery('What is the minimum punishment for credit card fraud?')">
              <q-item-section>
                <q-item-label>
                  What is the minimum punishment for credit card fraud?
                </q-item-label>
                <q-item-label caption>
                  Penalties for fraud-related offences
                </q-item-label>
              </q-item-section>
            </q-item>

            <q-item clickable v-ripple @click="setQuery('What determines fitness to stand trial?')">
              <q-item-section>
                <q-item-label>
                  What determines fitness to stand trial?
                </q-item-label>
                <q-item-label caption>
                  Legal criteria for mental fitness in court
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <q-btn
          color="primary"
          @click="runQuery"
          :loading="loading"
          :disable="!query || !apiKey"
          class="input-btn"
        >
          <template v-slot:default>
            Search
          </template>

          <template v-slot:loading>
            <div class="row items-center no-wrap">
              <q-spinner-hourglass size="20px" class="q-mr-sm" />
              <span>Searching...</span>
            </div>
          </template>
        </q-btn>
      </q-card>

      <!-- Results -->
      <q-card v-if="docs.length" class="q-pa-md">
        <div class="text-h6 q-mb-md">📚 Retrieved Documents</div>

        <div
          v-for="(doc, i) in docs"
          :key="i"
          class="q-mb-md"
        >
          <div class="text-subtitle2">
            [{{ i + 1 }}] {{ doc.metadata?.section || "Unknown Section" }}
          </div>

          <div class="text-caption text-grey">
            Score: {{ doc.score ?? "N/A" }}
          </div>

          <div class="text-body2 q-mt-sm">
            {{ doc.page_content?.slice(0, 500) }}
          </div>

          <q-separator class="q-my-md" />
        </div>
      </q-card>

      <!-- Empty state -->
      <q-card v-else-if="!loading" class="q-pa-md text-center text-grey">
        No results yet. Run a query to see retrieved documents.
      </q-card>

    </div>
  </q-page>
</template>

<script>
export default {
  name: "IndexPage",

  data() {
    return {
      query: "",
      apiKey: "",
      docs: [],
      loading: false,
      API_URL: "https://ragdemo.shorecode.org:8888/query",
    }
  },

  methods: {
    setQuery(q) {
      this.query = q
    },

    async runQuery() {
      if (!this.query || !this.apiKey) return

      this.loading = true
      this.docs = []

      try {
        const res = await fetch(this.API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: this.query,
            api_key: this.apiKey,
          }),
        })

        const data = await res.json()
        this.docs = data.retrieved_docs || []

      } catch (err) {
        this.$q.notify({
          type: "negative",
          message: err.message,
        })
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
<style scoped>
.input-btn {
  width: 160px;
}
</style>
