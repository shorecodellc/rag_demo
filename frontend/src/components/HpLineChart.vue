<template>
  <div class="hp-chart-container" :style="{ height: height }">
    <canvas ref="canvas"></canvas>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Filler)

export default defineComponent({
  name: 'HpLineChart',

  props: {
    labels:   { type: Array, required: true },
    datasets: { type: Array, required: true },
    height:   { type: String, default: '300px' },
    yLabel:   { type: String, default: '' },
  },

  data () {
    return { chart: null }
  },

  watch: {
    datasets: { deep: true, handler () { this.updateChart() } }
  },

  mounted () { this.initChart() },
  beforeUnmount () { if (this.chart) this.chart.destroy() },

  methods: {
    initChart () {
      const ctx = this.$refs.canvas.getContext('2d')
      this.chart = new Chart(ctx, {
        type: 'line',
        data: { labels: this.labels, datasets: this.datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { intersect: false, mode: 'index' },
          plugins: {
            legend: { position: 'top' },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${ctx.formattedValue}` } }
          },
          scales: {
            x: { grid: { color: '#f0f0f0' } },
            y: {
              grid: { color: '#f0f0f0' },
              title: { display: !!this.yLabel, text: this.yLabel }
            }
          }
        }
      })
    },
    updateChart () {
      if (!this.chart) return
      this.chart.data.labels = this.labels
      this.chart.data.datasets = this.datasets
      this.chart.update()
    }
  }
})
</script>

<style scoped>
.hp-chart-container { position: relative; width: 100%; }
</style>
