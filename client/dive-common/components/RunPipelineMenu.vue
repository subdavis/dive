<script lang="ts">
import {
  defineComponent, computed, PropType, ref, onBeforeMount,
} from '@vue/composition-api';
import {
  Pipelines,
  Pipe,
  useApi,
  SubType,
} from 'dive-common/apispec';
import JobLaunchDialog from 'dive-common/components/JobLaunchDialog.vue';
import { stereoPipelineMarker, multiCamPipelineMarkers } from 'dive-common/constants';
import { useRequest } from 'dive-common/use';

export default defineComponent({
  name: 'RunPipelineMenu',

  components: { JobLaunchDialog },

  props: {
    selectedDatasetIds: {
      type: Array as PropType<string[]>,
      default: () => [],
    },
    buttonOptions: {
      type: Object,
      default: () => ({}),
    },
    menuOptions: {
      type: Object,
      default: () => ({}),
    },
    /* Which pipelines to show based on dataset subtypes */
    subTypeList: {
      type: Array as PropType<SubType[]>,
      default: () => ([]),
    },
    /* Which pipelines to show based on how many cameras they accept */
    cameraNumbers: {
      type: Array as PropType<number[]>,
      default: () => ([1]),
    },
  },

  setup(props) {
    const { runPipeline, getPipelineList } = useApi();
    const unsortedPipelines = ref({} as Pipelines);
    const selectedPipe = ref(null as Pipe | null);
    const camNumberStringArray = computed(() => props.cameraNumbers.map((v) => v.toString()));
    const {
      request: _runPipelineRequest,
      reset: dismissLaunchDialog,
      state: jobState,
    } = useRequest();

    const successMessage = computed(() => (
      `Started ${selectedPipe.value?.name} on ${props.selectedDatasetIds.length} dataset(s).`));

    onBeforeMount(async () => {
      unsortedPipelines.value = await getPipelineList();
    });

    const pipelines = computed(() => {
      const sortedPipelines = {} as Pipelines;
      Object.entries(unsortedPipelines.value).forEach(([name, category]) => {
        category.pipes.sort((a, b) => {
          const aName = a.name.toLowerCase();
          const bName = b.name.toLowerCase();
          if (aName > bName) {
            return 1;
          }
          if (aName < bName) {
            return -1;
          }
          return 0;
        });
        // Filter out unsupported pipelines based on subTypeList
        // measurement can only be operated on stereo subtypes
        if (props.subTypeList.every((item) => item === 'stereo') && (name === stereoPipelineMarker)) {
          sortedPipelines[name] = category;
        } else if (props.subTypeList.every((item) => item === 'multicam') && (multiCamPipelineMarkers.includes(name))) {
          const pipelineExpectedCameraCount = name.split('-')[0];
          if (camNumberStringArray.value.includes(pipelineExpectedCameraCount)) {
            sortedPipelines[name] = category;
          }
        } else if (props.subTypeList.every((item) => item === null)
        && name !== stereoPipelineMarker && !multiCamPipelineMarkers.includes(name)) {
          sortedPipelines[name] = category;
        }
      });
      return sortedPipelines;
    });

    const pipelinesNotRunnable = computed(() => (
      props.selectedDatasetIds.length < 1 || pipelines.value === null
    ));

    async function runPipelineOnSelectedItem(pipeline: Pipe) {
      if (props.selectedDatasetIds.length === 0) {
        throw new Error('No selected datasets to run on');
      }
      selectedPipe.value = pipeline;
      await _runPipelineRequest(() => Promise.all(
        props.selectedDatasetIds.map((id) => runPipeline(id, pipeline)),
      ));
    }

    function pipeTypeDisplay(pipeType: string) {
      switch (pipeType) {
        case 'trained':
          return 'trained';
        case 'utility':
        case 'generate':
          return 'utilities';
        default:
          return `${pipeType}s`;
      }
    }

    return {
      jobState,
      pipelines,
      pipelinesNotRunnable,
      successMessage,
      dismissLaunchDialog,
      pipeTypeDisplay,
      runPipelineOnSelectedItem,
    };
  },
});
</script>

<template>
  <div>
    <v-menu
      max-width="230"
      v-bind="menuOptions"
      :close-on-content-click="false"
    >
      <template v-slot:activator="{ on: menuOn }">
        <v-tooltip
          bottom
          :disabled="menuOptions.offsetX"
        >
          <template #activator="{ on: tooltipOn }">
            <v-btn
              v-bind="buttonOptions"
              :disabled="pipelinesNotRunnable"
              v-on="{ ...tooltipOn, ...menuOn }"
            >
              <v-icon>
                mdi-pipe
              </v-icon>
              <span
                v-show="!$vuetify.breakpoint.mdAndDown || buttonOptions.block"
                class="pl-1"
              >
                Run pipeline
              </span>
              <v-spacer />
              <v-icon v-if="menuOptions.right">
                mdi-chevron-right
              </v-icon>
            </v-btn>
          </template>
          <span>Run CV algorithm pipelines on this data</span>
        </v-tooltip>
      </template>

      <template>
        <v-card
          v-if="pipelines"
          outlined
        >
          <v-card-title>
            VIAME Pipelines
          </v-card-title>

          <v-card-text class="pb-0">
            Choose a pipeline type. Check the
            <a
              href="https://kitware.github.io/dive/Pipeline-Documentation/"
              target="_blank"
            >docs</a>
            for more information about these options.
          </v-card-text>
          <v-row class="px-3">
            <v-col
              v-for="(pipeType) in Object.keys(pipelines)"
              :key="pipeType"
              cols="12"
            >
              <v-menu
                :key="pipeType"
                offset-x
                right
              >
                <template v-slot:activator="{ on }">
                  <v-btn
                    depressed
                    block
                    v-on="on"
                  >
                    {{ pipeTypeDisplay(pipeType) }}
                    <v-icon
                      right
                      color="accent"
                      class="ml-2"
                    >
                      mdi-menu-right
                    </v-icon>
                  </v-btn>
                </template>

                <v-list
                  dense
                  outlined
                  style="overflow-y:auto; max-height:85vh"
                >
                  <v-list-item
                    v-for="(pipeline) in pipelines[pipeType].pipes"
                    :key="`${pipeline.name}-${pipeline.pipe}`"
                    @click="runPipelineOnSelectedItem(pipeline)"
                  >
                    <v-list-item-title class="font-weight-regular">
                      {{ pipeline.name }}
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-col>
          </v-row>
        </v-card>
      </template>
    </v-menu>
    <JobLaunchDialog
      :value="jobState.count > 0"
      :loading="jobState.loading"
      :error="jobState.error"
      :message="successMessage"
      @close="dismissLaunchDialog"
    />
  </div>
</template>
