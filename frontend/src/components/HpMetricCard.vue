<template>
  <q-card flat bordered class="hp-metric-card">
    <q-card-section class="q-pa-md">
      <div class="row items-center no-wrap">
        <div class="col">
          <div class="text-caption text-grey-6 text-uppercase q-mb-xs">{{ label }}</div>
          <div class="text-h4 text-weight-bold" :class="valueClass">{{ formattedValue }}</div>
          <div v-if="subtitle" class="text-caption text-grey-6 q-mt-xs">{{ subtitle }}</div>
        </div>
        <div class="col-auto q-ml-md">
          <q-avatar :color="iconBg" text-color="white" size="48px">
            <q-icon :name="icon" size="24px" />
          </q-avatar>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'HpMetricCard',

  props: {
    label:    { type: String, required: true },
    value:    { type: [Number, String], required: true },
    format:   { type: String, default: 'number' },
    decimals: { type: Number, default: 2 },
    subtitle: { type: String, default: '' },
    icon:     { type: String, default: 'info' },
    iconBg:   { type: String, default: 'green-7' },
    positive: { type: Boolean, default: null }
  },

  computed: {
    formattedValue () {
      const v = this.value
      if (this.format === 'percent') return `${(v * 100).toFixed(1)}%`
      if (this.format === 'roi')     return `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}%`
      if (this.format === 'number')  return typeof v === 'number' ? v.toFixed(this.decimals) : v
      return String(v)
    },
    valueClass () {
      if (this.positive === null) return 'text-dark'
      return this.positive ? 'hp-positive' : 'hp-negative'
    }
  }
})
</script>

<style scoped>
.hp-metric-card {
  border-radius: 12px;
  transition: box-shadow 0.2s;
}
.hp-metric-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
</style>
