<template>
  <q-page class="q-pa-md flex flex-center">
    <div style="width: 100%; max-width: 900px;">

      <!-- Header -->
      <div class="text-h4 q-mb-xs">
        LangGraph Multi-Agent Generator
      </div>
      <div class="text-subtitle1 text-grey q-mb-xs">
        Describe your agent pipeline and get a complete, runnable Python implementation.
      </div>
      <div class="text-caption text-grey q-mb-md made-with">
        This module was built with
        <a href="https://claude.ai/code" target="_blank" rel="noopener" class="text-primary">Claude Code</a>
        by Kevin Fink
      </div>

      <!-- Input Card -->
      <q-card class="q-pa-md q-mb-md">
        <q-input
          v-model="apiKey"
          type="password"
          label="OpenAI API Key"
          filled
          class="q-mb-md"
        />

        <q-input
          v-model="description"
          type="textarea"
          label="Describe your multi-agent pipeline"
          hint="e.g. 'A research agent that searches the web, summarises findings, and verifies facts'"
          filled
          autogrow
          class="q-mb-md"
        />

        <!-- Example descriptions -->
        <div class="q-mb-md">
          <div class="text-subtitle2 q-mb-sm text-grey">Examples:</div>
          <div class="row q-gutter-sm">
            <q-chip
              v-for="ex in examples"
              :key="ex"
              clickable
              color="blue-grey-1"
              text-color="dark"
              @click="description = ex"
            >
              {{ ex }}
            </q-chip>
          </div>
        </div>

        <!-- Advanced options -->
        <q-expansion-item
          label="Advanced options"
          dense
          class="q-mb-md text-grey"
        >
          <div class="q-pa-sm q-gutter-md">
            <q-select
              v-model="model"
              :options="modelOptions"
              label="Model"
              filled
              dense
              style="max-width: 260px"
            />

            <div>
              <div class="text-caption q-mb-xs">
                Confidence threshold: {{ confidenceThreshold.toFixed(2) }}
              </div>
              <q-slider
                v-model="confidenceThreshold"
                :min="0.5"
                :max="1.0"
                :step="0.05"
                label
                color="primary"
                style="max-width: 300px"
              />
            </div>

            <q-input
              v-model.number="maxIterations"
              type="number"
              label="Max retry iterations"
              filled
              dense
              style="max-width: 160px"
              :min="1"
              :max="10"
            />
          </div>
        </q-expansion-item>

        <q-btn
          color="primary"
          :loading="loading"
          :disable="!description || !apiKey"
          class="generate-btn"
          @click="generate"
        >
          <template v-slot:default>Generate Pipeline</template>
          <template v-slot:loading>
            <div class="row items-center no-wrap">
              <q-spinner-hourglass size="20px" class="q-mr-sm" />
              <span>Generating...</span>
            </div>
          </template>
        </q-btn>
      </q-card>

      <!-- Streaming progress -->
      <q-card v-if="loading || (streamBuffer && !generatedCode)" class="q-pa-md q-mb-md">
        <div class="row items-center q-mb-sm">
          <q-spinner-dots color="primary" size="20px" class="q-mr-sm" />
          <span class="text-subtitle2">Generating your pipeline...</span>
        </div>
        <q-linear-progress indeterminate color="primary" class="q-mb-md" />
        <pre class="stream-preview text-caption">{{ streamBuffer }}</pre>
      </q-card>

      <!-- Result card -->
      <q-card v-if="generatedCode" class="q-pa-md">
        <div class="row items-center justify-between q-mb-md">
          <div class="text-h6">Generated Pipeline</div>
          <div class="row q-gutter-sm">
            <q-btn flat dense icon="content_copy" label="Copy" @click="copyCode" />
            <q-btn flat dense icon="download" label="Download .py" @click="downloadCode" />
          </div>
        </div>

        <!-- Node summary chips -->
        <div v-if="nodeNames.length" class="q-mb-md">
          <div class="text-caption text-grey q-mb-xs">Detected nodes:</div>
          <q-chip
            v-for="node in nodeNames"
            :key="node"
            color="primary"
            text-color="white"
            dense
            class="q-mr-xs"
          >
            {{ node }}
          </q-chip>
        </div>

        <!-- Syntax-highlighted code block -->
        <pre class="code-block"><code v-html="highlightedCode" /></pre>
      </q-card>

    </div>
  </q-page>
</template>

<script>
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'

hljs.registerLanguage('python', python)

const API_BASE = 'https://ragdemo.shorecode.org:8888'

export default {
  name: 'CodegenPage',

  data() {
    return {
      apiKey: '',
      description: '',
      model: 'gpt-5.4',
      confidenceThreshold: 0.85,
      maxIterations: 3,
      loading: false,
      streamBuffer: '',
      generatedCode: '',
      nodeNames: [],
      modelOptions: ['gpt-5.4', 'gpt-5.4-mini', 'gpt-5.4-nano'],
      examples: [
        'A research agent that searches the web, summarises findings, and verifies facts',
        'A customer support triage agent that classifies tickets and drafts responses',
        'A code review agent that analyses Python code for bugs, style, and security issues',
        'A data analysis agent that extracts insights from CSV data and generates a report',
      ],
    }
  },

  computed: {
    highlightedCode() {
      if (!this.generatedCode) return ''
      return hljs.highlight(this.generatedCode, { language: 'python' }).value
    },
  },

  methods: {
    async generate() {
      if (!this.description || !this.apiKey) return

      this.loading = true
      this.streamBuffer = ''
      this.generatedCode = ''
      this.nodeNames = []

      const body = JSON.stringify({
        description: this.description,
        api_key: this.apiKey,
        model: this.model,
        confidence_threshold: this.confidenceThreshold,
        max_iterations: this.maxIterations,
      })

      try {
        const response = await fetch(`${API_BASE}/codegen/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body,
        })

        if (!response.ok) {
          const err = await response.json()
          throw new Error(err.detail || `HTTP ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete SSE lines
          const lines = buffer.split('\n')
          buffer = lines.pop() // keep incomplete line in buffer

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const payload = line.slice(6).trim()
            if (!payload) continue

            let parsed
            try {
              parsed = JSON.parse(payload)
            } catch {
              continue
            }

            if (parsed.error) {
              throw new Error(parsed.error)
            }

            if (parsed.done) {
              this.nodeNames = parsed.node_names || []
              this.generatedCode = this.streamBuffer
              this.loading = false
              await this.$nextTick()
              this.scrollToResult()
            } else if (parsed.token) {
              this.streamBuffer += parsed.token
              await this.$nextTick()
              this.scrollStreamPreview()
            }
          }
        }

        // Fallback: if done event never fired but we have content
        if (this.loading && this.streamBuffer) {
          this.generatedCode = this.streamBuffer
          this.loading = false
        }
      } catch (err) {
        this.loading = false
        this.$q.notify({ type: 'negative', message: err.message })
      }
    },

    scrollStreamPreview() {
      const el = this.$el.querySelector('.stream-preview')
      if (el) el.scrollTop = el.scrollHeight
    },

    scrollToResult() {
      const el = this.$el.querySelector('.code-block')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },

    copyCode() {
      navigator.clipboard.writeText(this.generatedCode).then(() => {
        this.$q.notify({ type: 'positive', message: 'Copied to clipboard' })
      })
    },

    downloadCode() {
      const blob = new Blob([this.generatedCode], { type: 'text/x-python' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'langgraph_pipeline.py'
      a.click()
      URL.revokeObjectURL(url)
    },
  },
}
</script>

<style scoped>
.generate-btn {
  min-width: 180px;
}

.stream-preview {
  font-family: monospace;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

.code-block {
  background: #1e1e2e;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family: 'Fira Code', 'Cascadia Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre;
  margin: 0;
}

.code-block :deep(code) {
  background: transparent;
  color: #cdd6f4;
  padding: 0;
  white-space: pre;
}

.made-with {
  font-style: italic;
}

.made-with a {
  text-decoration: none;
}

.made-with a:hover {
  text-decoration: underline;
}
</style>
