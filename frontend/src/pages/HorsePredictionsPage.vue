<template>
  <q-page padding>
    <div class="hp-page-title">Horse Predictions</div>
    <div class="text-grey-6 q-mb-md">LightGBM walk-forward backtest analytics</div>

    <q-tabs
      v-model="tab"
      dense
      align="left"
      active-color="green-8"
      indicator-color="green-8"
      class="q-mb-lg"
    >
      <q-tab name="dashboard" icon="dashboard"  label="Dashboard" />
      <q-tab name="backtest"  icon="show_chart"  label="Backtest"  />
      <q-tab name="picks"     icon="star"         label="Top Picks" />
      <q-tab name="features"  icon="bar_chart"    label="Features"  />
    </q-tabs>

    <q-tab-panels v-model="tab" animated keep-alive>

      <!-- ── DASHBOARD ────────────────────────────────────────────── -->
      <q-tab-panel name="dashboard" class="q-pa-none">
        <div v-if="dash.loading" class="flex flex-center q-py-xl">
          <q-spinner-dots color="green-7" size="48px" />
        </div>
        <div v-else-if="dash.error" class="text-negative q-pa-md">
          <q-icon name="error" /> {{ dash.error }}
        </div>
        <template v-else>
          <div class="row q-col-gutter-md q-mb-xl">
            <div class="col-12 col-sm-6 col-md-3">
              <HpMetricCard label="Weighted ROI" :value="dash.metrics.weighted_roi" format="roi"
                subtitle="Uniform-odds simulation" icon="trending_up" icon-bg="green-7"
                :positive="dash.metrics.weighted_roi >= 0" />
            </div>
            <div class="col-12 col-sm-6 col-md-3">
              <HpMetricCard label="Hit Rate" :value="dash.metrics.hit_rate" format="percent"
                subtitle="vs 11% random baseline" icon="sports_score" icon-bg="blue-7" :positive="true" />
            </div>
            <div class="col-12 col-sm-6 col-md-3">
              <HpMetricCard label="Mean AUC" :value="dash.metrics.mean_auc" format="number" :decimals="4"
                subtitle="Out-of-sample ranking quality" icon="area_chart" icon-bg="purple-6"
                :positive="dash.metrics.mean_auc > 0.6" />
            </div>
            <div class="col-12 col-sm-6 col-md-3">
              <HpMetricCard label="Total Bets" :value="dash.metrics.total_bets" format="string"
                :subtitle="`across ${dash.metrics.total_folds} folds`" icon="casino" icon-bg="amber-8" />
            </div>
          </div>

          <div class="row q-col-gutter-md q-mb-xl">
            <div class="col-12 col-sm-4">
              <HpMetricCard label="Mean EV" :value="dash.metrics.mean_ev" format="number" :decimals="3"
                subtitle="Expected value vs uniform baseline" icon="bolt" icon-bg="orange-7"
                :positive="dash.metrics.mean_ev > 0" />
            </div>
            <div class="col-12 col-sm-4">
              <HpMetricCard label="Mean Brier Score" :value="dash.metrics.mean_brier" format="number" :decimals="4"
                subtitle="Probability calibration (lower = better)" icon="tune" icon-bg="teal-6" />
            </div>
            <div class="col-12 col-sm-4">
              <HpMetricCard label="Test Period" :value="dashDateRange" format="string"
                subtitle="Walk-forward test window" icon="date_range" icon-bg="grey-6" />
            </div>
          </div>

          <q-card flat bordered class="q-mb-xl">
            <q-card-section>
              <div class="text-subtitle1 text-weight-medium q-mb-sm">ROI by Fold</div>
              <HpLineChart v-if="dash.foldData.length" :labels="dashFoldLabels" :datasets="dashRoiDatasets"
                height="260px" y-label="ROI (×)" />
            </q-card-section>
          </q-card>

          <q-banner rounded class="bg-blue-1 text-blue-9">
            <template #avatar><q-icon name="info" color="blue-7" /></template>
            ROI is computed against <strong>uniform fair-value odds</strong> (field size − 1).
            A {{ (dash.metrics.hit_rate * 100).toFixed(1) }}% hit rate against an 11% baseline confirms genuine predictive signal.
          </q-banner>
        </template>
      </q-tab-panel>

      <!-- ── BACKTEST ─────────────────────────────────────────────── -->
      <q-tab-panel name="backtest" class="q-pa-none">
        <div v-if="bt.loading" class="flex flex-center q-py-xl">
          <q-spinner-dots color="green-7" size="48px" />
        </div>
        <div v-else-if="bt.error" class="text-negative q-pa-md">
          <q-icon name="error" /> {{ bt.error }}
        </div>
        <template v-else>
          <div class="row q-col-gutter-md q-mb-xl">
            <div class="col-12 col-md-6">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-subtitle1 text-weight-medium q-mb-sm">ROI per Fold</div>
                  <HpLineChart :labels="btLabels" :datasets="btRoiDatasets" height="240px" y-label="ROI (×)" />
                </q-card-section>
              </q-card>
            </div>
            <div class="col-12 col-md-6">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-subtitle1 text-weight-medium q-mb-sm">AUC & Hit Rate per Fold</div>
                  <HpLineChart :labels="btLabels" :datasets="btAucDatasets" height="240px" y-label="Score" />
                </q-card-section>
              </q-card>
            </div>
          </div>

          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1 text-weight-medium q-mb-md">Fold Details</div>
              <q-table :rows="bt.rows" :columns="btColumns" row-key="fold" flat dense :pagination="{ rowsPerPage: 25 }">
                <template #body-cell-roi="props">
                  <q-td :props="props" :class="props.value >= 0 ? 'hp-positive' : 'hp-negative'">
                    {{ fmtRoi(props.value) }}
                  </q-td>
                </template>
                <template #body-cell-hit_rate="props">
                  <q-td :props="props">{{ fmtPct(props.value) }}</q-td>
                </template>
                <template #body-cell-roc_auc="props">
                  <q-td :props="props">{{ props.value?.toFixed(4) }}</q-td>
                </template>
              </q-table>
            </q-card-section>
          </q-card>
        </template>
      </q-tab-panel>

      <!-- ── TOP PICKS ────────────────────────────────────────────── -->
      <q-tab-panel name="picks" class="q-pa-none">
        <div v-if="picks.loading" class="flex flex-center q-py-xl">
          <q-spinner-dots color="green-7" size="48px" />
        </div>
        <div v-else-if="picks.error" class="text-negative q-pa-md">
          <q-icon name="error" /> {{ picks.error }}
        </div>
        <template v-else>
          <div class="row q-col-gutter-sm q-mb-md items-center">
            <div class="col-12 col-sm-4">
              <q-input v-model="picks.search" dense outlined placeholder="Search horse / jockey / trainer" clearable>
                <template #prepend><q-icon name="search" /></template>
              </q-input>
            </div>
            <div class="col-12 col-sm-3">
              <q-select v-model="picks.goingFilter" :options="picksGoingOptions" dense outlined clearable
                emit-value map-options label="Going" />
            </div>
            <div class="col-auto">
              <q-chip v-for="s in picksSummaryStats" :key="s.label" :color="s.color" text-color="white" size="md">
                {{ s.label }}: {{ s.value }}
              </q-chip>
            </div>
          </div>

          <q-card flat bordered>
            <q-table :rows="picksFiltered" :columns="picksColumns" row-key="idx" flat :pagination="{ rowsPerPage: 20 }">
              <template #body-cell-target_win="props">
                <q-td :props="props">
                  <q-badge :color="props.value === 1 ? 'green-7' : 'grey-5'" :label="props.value === 1 ? 'WIN' : 'Lost'" />
                </q-td>
              </template>
              <template #body-cell-win_prob_norm="props">
                <q-td :props="props">
                  <div class="row items-center no-wrap">
                    <q-linear-progress :value="props.value" color="green-7" track-color="grey-3"
                      size="8px" class="col q-mr-sm" style="max-width:80px" />
                    {{ (props.value * 100).toFixed(1) }}%
                  </div>
                </q-td>
              </template>
              <template #body-cell-ev="props">
                <q-td :props="props" :class="props.value >= 1 ? 'hp-positive' : 'hp-neutral'">
                  {{ props.value?.toFixed(3) }}
                </q-td>
              </template>
            </q-table>
          </q-card>
        </template>
      </q-tab-panel>

      <!-- ── FEATURES ──────────────────────────────────────────────── -->
      <q-tab-panel name="features" class="q-pa-none">
        <div v-if="feat.loading" class="flex flex-center q-py-xl">
          <q-spinner-dots color="green-7" size="48px" />
        </div>
        <div v-else-if="feat.error" class="text-negative q-pa-md">
          <q-icon name="error" /> {{ feat.error }}
        </div>
        <template v-else>
          <div class="row q-col-gutter-md">
            <div class="col-12 col-lg-7">
              <q-card flat bordered>
                <q-card-section>
                  <div class="row items-center q-mb-sm">
                    <div class="text-subtitle1 text-weight-medium col">Top {{ feat.chartCount }} Features</div>
                    <q-slider v-model="feat.chartCount" :min="5" :max="Math.min(30, feat.rows.length)"
                      :step="5" label color="green-7" style="width:140px" class="q-mr-sm" />
                  </div>
                  <HpBarChart :labels="featChartLabels" :datasets="featChartDatasets"
                    :height="featBarHeight" :horizontal="true" />
                </q-card-section>
              </q-card>
            </div>
            <div class="col-12 col-lg-5">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-subtitle1 text-weight-medium q-mb-md">All Features</div>
                  <q-table :rows="featTableRows" :columns="featColumns" row-key="feature" flat dense
                    :pagination="{ rowsPerPage: 20 }">
                    <template #body-cell-pct="props">
                      <q-td :props="props">
                        <div class="row items-center no-wrap">
                          <q-linear-progress :value="props.value / 100" color="green-7" track-color="grey-3"
                            size="8px" style="width:80px" class="q-mr-sm" />
                          {{ props.value.toFixed(1) }}%
                        </div>
                      </q-td>
                    </template>
                  </q-table>
                </q-card-section>
              </q-card>
            </div>
          </div>

          <q-card flat bordered class="q-mt-md">
            <q-card-section>
              <div class="text-subtitle2 q-mb-sm">Feature Groups</div>
              <div class="row q-col-gutter-sm">
                <div v-for="g in featGroups" :key="g.label" class="col-auto">
                  <q-chip :color="g.color" text-color="white" size="sm">{{ g.label }}</q-chip>
                  <span class="text-caption text-grey-6 q-ml-xs">{{ g.desc }}</span>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </template>
      </q-tab-panel>

    </q-tab-panels>
  </q-page>
</template>

<script>
import { defineComponent } from 'vue'
import { hpApi } from 'boot/axios'
import HpMetricCard from 'components/HpMetricCard.vue'
import HpLineChart from 'components/HpLineChart.vue'
import HpBarChart from 'components/HpBarChart.vue'

export default defineComponent({
  name: 'HorsePredictionsPage',
  components: { HpMetricCard, HpLineChart, HpBarChart },

  data () {
    return {
      tab: 'dashboard',

      dash: {
        loading: true, error: null,
        metrics: {}, foldData: [],
      },

      bt: {
        loading: true, error: null, rows: [],
        columns: [
          { name: 'fold',       label: 'Fold',       field: 'fold',       align: 'center', sortable: true },
          { name: 'test_start', label: 'Test Start', field: 'test_start', align: 'left',   sortable: true },
          { name: 'test_end',   label: 'Test End',   field: 'test_end',   align: 'left',   sortable: true },
          { name: 'n_train',    label: 'Train Rows', field: 'n_train',    align: 'right',  sortable: true },
          { name: 'n_test',     label: 'Test Rows',  field: 'n_test',     align: 'right',  sortable: true },
          { name: 'n_bets',     label: 'Bets',       field: 'n_bets',     align: 'right',  sortable: true },
          { name: 'roi',        label: 'ROI',        field: 'roi',        align: 'right',  sortable: true },
          { name: 'hit_rate',   label: 'Hit %',      field: 'hit_rate',   align: 'right',  sortable: true },
          { name: 'avg_ev',     label: 'Avg EV',     field: 'avg_ev',     align: 'right',  sortable: true, format: v => v?.toFixed(3) },
          { name: 'roc_auc',    label: 'AUC',        field: 'roc_auc',    align: 'right',  sortable: true },
          { name: 'brier',      label: 'Brier',      field: 'brier',      align: 'right',  sortable: true, format: v => v?.toFixed(4) },
        ]
      },

      picks: {
        loading: true, error: null, rows: [],
        search: '', goingFilter: null,
        columns: [
          { name: 'date',          label: 'Date',       field: 'date',          align: 'left',   sortable: true },
          { name: 'raceno',        label: 'Race',       field: 'raceno',        align: 'center', sortable: true },
          { name: 'horse',         label: 'Horse',      field: 'horse',         align: 'left',   sortable: true },
          { name: 'jockey',        label: 'Jockey',     field: 'jockey',        align: 'left',   sortable: true },
          { name: 'trainer',       label: 'Trainer',    field: 'trainer',       align: 'left',   sortable: true },
          { name: 'draw',          label: 'Draw',       field: 'draw',          align: 'center', sortable: true },
          { name: 'distance',      label: 'Dist (m)',   field: 'distance',      align: 'right',  sortable: true },
          { name: 'going',         label: 'Going',      field: 'going',         align: 'left',   sortable: true },
          { name: 'field_size',    label: 'Field',      field: 'field_size',    align: 'center', sortable: true },
          { name: 'win_prob_norm', label: 'Win Prob',   field: 'win_prob_norm', align: 'left',   sortable: true },
          { name: 'ev',            label: 'EV',         field: 'ev',            align: 'right',  sortable: true },
          { name: 'plc',           label: 'Actual Pos', field: 'plc',           align: 'center', sortable: true },
          { name: 'target_win',    label: 'Result',     field: 'target_win',    align: 'center', sortable: true },
        ]
      },

      feat: {
        loading: true, error: null, rows: [], chartCount: 20,
        columns: [
          { name: 'rank',       label: '#',          field: 'rank',       align: 'center', sortable: true },
          { name: 'feature',    label: 'Feature',    field: 'feature',    align: 'left',   sortable: true },
          { name: 'importance', label: 'Importance', field: 'importance', align: 'right',  sortable: true },
          { name: 'pct',        label: '% of Total', field: 'pct',        align: 'left',   sortable: true },
        ],
        groups: [
          { label: 'Draw',    color: 'teal-6',   desc: 'Barrier position & bias' },
          { label: 'Horse',   color: 'green-7',  desc: 'Rolling win/place/avg finish' },
          { label: 'Jockey',  color: 'blue-7',   desc: 'Rolling stats per jockey' },
          { label: 'Trainer', color: 'purple-6', desc: 'Rolling stats per trainer' },
          { label: 'Race',    color: 'orange-7', desc: 'Distance, going, course, field size' },
          { label: 'Suit',    color: 'brown-5',  desc: 'Horse suitability for condition' },
          { label: 'Gear',    color: 'grey-6',   desc: 'Equipment flags' },
        ]
      },
    }
  },

  computed: {
    // dashboard
    dashFoldLabels () { return this.dash.foldData.map(r => r.test_start) },
    dashDateRange () {
      if (!this.dash.metrics.date_range) return '—'
      return `${this.dash.metrics.date_range.start} → ${this.dash.metrics.date_range.end}`
    },
    dashRoiDatasets () {
      return [{
        label: 'ROI',
        data: this.dash.foldData.map(r => r.roi),
        borderColor: '#1a6b3a',
        backgroundColor: 'rgba(26,107,58,0.1)',
        fill: true, tension: 0.3, pointRadius: 4,
      }]
    },

    // backtest
    btRoiDatasets () {
      return [{
        label: 'ROI', data: this.bt.rows.map(r => r.roi),
        borderColor: '#1a6b3a', backgroundColor: 'rgba(26,107,58,0.12)',
        fill: true, tension: 0.3, pointRadius: 4,
      }]
    },
    btAucDatasets () {
      return [
        { label: 'AUC', data: this.bt.rows.map(r => r.roc_auc),
          borderColor: '#6a5acd', tension: 0.3, pointRadius: 4, fill: false },
        { label: 'Hit Rate', data: this.bt.rows.map(r => r.hit_rate),
          borderColor: '#f0b429', tension: 0.3, pointRadius: 4, fill: false },
      ]
    },
    btLabels () { return this.bt.rows.map(r => r.test_start) },

    // picks
    picksGoingOptions () {
      const vals = [...new Set(this.picks.rows.map(r => r.going).filter(Boolean))]
      return vals.map(v => ({ label: v, value: v }))
    },
    picksFiltered () {
      let data = this.picks.rows
      if (this.picks.search) {
        const q = this.picks.search.toLowerCase()
        data = data.filter(r =>
          (r.horse  || '').toLowerCase().includes(q) ||
          (r.jockey || '').toLowerCase().includes(q) ||
          (r.trainer|| '').toLowerCase().includes(q)
        )
      }
      if (this.picks.goingFilter) data = data.filter(r => r.going === this.picks.goingFilter)
      return data.map((r, i) => ({ ...r, idx: i }))
    },
    picksSummaryStats () {
      const hits  = this.picksFiltered.filter(r => r.target_win === 1).length
      const total = this.picksFiltered.length
      return [
        { label: 'Showing', value: total, color: 'grey-7' },
        { label: 'Winners', value: hits,  color: 'green-7' },
        { label: 'Hit %', value: total ? `${((hits / total) * 100).toFixed(1)}%` : '—', color: 'blue-7' },
      ]
    },

    // features
    featTotalImportance () { return this.feat.rows.reduce((s, r) => s + r.importance, 0) },
    featTableRows () {
      return this.feat.rows.map((r, i) => ({
        ...r, rank: i + 1,
        pct: this.featTotalImportance ? (r.importance / this.featTotalImportance) * 100 : 0,
      }))
    },
    featTopRows () { return this.featTableRows.slice(0, this.feat.chartCount) },
    featChartLabels () { return this.featTopRows.map(r => r.feature) },
    featChartDatasets () {
      return [{
        label: 'Importance',
        data: this.featTopRows.map(r => r.importance),
        backgroundColor: this.featTopRows.map(r => this.colorForFeature(r.feature)),
        borderWidth: 0,
      }]
    },
    featBarHeight () { return `${this.feat.chartCount * 28 + 40}px` },
    featGroups () { return this.feat.groups },
    featColumns () { return this.feat.columns },
  },

  async created () {
    await Promise.all([
      this.loadDashboard(),
      this.loadBacktest(),
      this.loadPicks(),
      this.loadFeatures(),
    ])
  },

  methods: {
    async loadDashboard () {
      try {
        const [m, f] = await Promise.all([hpApi.get('/metrics'), hpApi.get('/roi-by-fold')])
        this.dash.metrics  = m.data
        this.dash.foldData = f.data
      } catch {
        this.dash.error = 'Could not load data. Is the horse predictions API running on port 8765?'
      } finally {
        this.dash.loading = false
      }
    },
    async loadBacktest () {
      try {
        const res = await hpApi.get('/backtest-summary')
        this.bt.rows = res.data
      } catch {
        this.bt.error = 'Could not load backtest data.'
      } finally {
        this.bt.loading = false
      }
    },
    async loadPicks () {
      try {
        const res = await hpApi.get('/top-picks?limit=500')
        this.picks.rows = res.data
      } catch {
        this.picks.error = 'Could not load picks.'
      } finally {
        this.picks.loading = false
      }
    },
    async loadFeatures () {
      try {
        const res = await hpApi.get('/feature-importance')
        this.feat.rows = res.data
      } catch {
        this.feat.error = 'Could not load feature importance.'
      } finally {
        this.feat.loading = false
      }
    },
    fmtRoi (v) { return v != null ? `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}%` : '—' },
    fmtPct (v) { return v != null ? `${(v * 100).toFixed(1)}%` : '—' },
    colorForFeature (name) {
      if (name.startsWith('draw'))    return '#0d9488'
      if (name.startsWith('horse'))   return '#1a6b3a'
      if (name.startsWith('jockey'))  return '#2563eb'
      if (name.startsWith('trainer')) return '#7c3aed'
      if (name.startsWith('gear'))    return '#9ca3af'
      return '#f59e0b'
    }
  }
})
</script>

<style>
.hp-positive { color: #1a6b3a; font-weight: 600; }
.hp-negative { color: #c0392b; font-weight: 600; }
.hp-neutral  { color: #555; }
.hp-page-title { font-size: 1.5rem; font-weight: 700; color: #1a1f2e; margin-bottom: 4px; }
</style>
