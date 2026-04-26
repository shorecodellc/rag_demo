<template>
  <div class="hp-chart-container" :style="{ height: height }">
    <canvas ref="canvas"></canvas>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import {
  Chart,
  BarController,
  BarElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from 'chart.js'

Chart.register(BarController, BarElement, LinearScale, CategoryScale, Tooltip, Legend)

export default defineComponent({
  name: 'HpBarChart',

  props: {
    labels:     { type: Array, required: true },
    datasets:   { type: Array, required: true },
    height:     { type: String, default: '300px' },
    horizontal: { type: Boolean, default: false },
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
        type: 'bar',
        data: { labels: this.labels, datasets: this.datasets },
        options: {
          indexAxis: this.horizontal ? 'y' : 'x',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.formattedValue}` } }
          },
          scales: {
            x: { grid: { color: '#f0f0f0' } },
            y: { grid: { color: '#f0f0f0' } }
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
