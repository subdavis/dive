<script lang="ts">
import Vue from 'vue';
import {
  defineComponent, reactive, computed, ref, Ref, watch,
} from '@vue/composition-api';

import { usePrompt } from 'dive-common/vue-utilities/prompt-service';
import { TrackWithContext } from '../use/useTrackFilters';

import { TrackId } from '../track';
import {
  useAllTypes,
  useCheckedTrackIds,
  useEditingMode,
  useHandler,
  useSelectedTrackId,
  useTrackMap,
  useFilteredTracks,
  useTypeStyling,
  useTime,
} from '../provides';
import TrackItem from './TrackItem.vue';

interface VirtualListItem {
  filteredTrack: TrackWithContext;
  selectedTrackId: number | null;
  checkedTrackIds: readonly number[];
  editingTrack: boolean;
  allTypes: readonly string[];
}

/* Magic numbers involved in height calculation */
const TrackListHeaderHeight = 52;

export default defineComponent({
  name: 'TrackList',

  props: {
    newTrackMode: {
      type: String,
      required: true,
    },
    newTrackType: {
      type: String,
      required: true,
    },
    lockTypes: {
      type: Boolean,
      default: false,
    },
    hotkeysDisabled: {
      type: Boolean,
      required: true,
    },
    height: {
      type: Number,
      default: 420,
    },
  },

  components: { TrackItem },

  setup(props) {
    const { prompt } = usePrompt();
    const allTypesRef = useAllTypes();
    const checkedTrackIdsRef = useCheckedTrackIds();
    const editingModeRef = useEditingMode();
    const selectedTrackIdRef = useSelectedTrackId();
    const trackMap = useTrackMap();
    const filteredTracksRef = useFilteredTracks();
    const typeStylingRef = useTypeStyling();
    const { frame: frameRef } = useTime();
    const {
      trackSelectNext, trackSplit, removeTrack, trackAdd,
    } = useHandler();

    const data = reactive({
      itemHeight: 70, // in pixelx
      settingsActive: false,
    });
    const virtualList = ref(null as null | Vue);

    const virtualListItems: Ref<readonly VirtualListItem[]> = computed(() => {
      const selectedTrackId = selectedTrackIdRef.value;
      const checkedTrackIds = checkedTrackIdsRef.value;
      const editingMode = editingModeRef.value;
      const allTypes = allTypesRef.value;
      return filteredTracksRef.value.map((filtered) => ({
        filteredTrack: filtered,
        selectedTrackId,
        checkedTrackIds,
        editingTrack: !!editingMode,
        allTypes,
      }));
    });

    const newTrackColor: Ref<string> = computed(() => {
      if (props.newTrackType !== 'unknown') {
        return typeStylingRef.value.color(props.newTrackType);
      }
      // Return default color
      return '';
    });

    function scrollToTrack(trackId: TrackId | null): void {
      if (trackId !== null && virtualList.value !== null) {
        const track = trackMap.get(trackId);
        if (track) {
          const offset = filteredTracksRef.value.findIndex(
            (filtered) => filtered.track.trackId === trackId,
          );
          if (offset === -1) {
            virtualList.value.$el.scrollTop = 0;
          } else {
            // try to show the selected track as the third track in the list
            virtualList.value.$el.scrollTop = (offset * data.itemHeight) - (2 * data.itemHeight);
          }
        }
      }
    }

    function scrollToSelectedTrack(): void {
      Vue.nextTick(() => scrollToTrack(selectedTrackIdRef.value));
    }

    // If we mount with selected we scroll to it automatically
    scrollToSelectedTrack();

    function scrollPreventDefault(
      element: HTMLElement,
      keyEvent: KeyboardEvent,
      direction: 'up' | 'down',
    ): void {
      if (virtualList.value !== null && element === virtualList.value.$el) {
        if (direction === 'up') {
          trackSelectNext(-1);
        } else if (direction === 'down') {
          trackSelectNext(1);
        }
        keyEvent.preventDefault();
      }
    }

    function getItemProps(item: VirtualListItem) {
      const confidencePair = item.filteredTrack.track.getType(
        item.filteredTrack.context.confidencePairIndex,
      );
      const trackType = confidencePair[0];
      const selected = item.selectedTrackId === item.filteredTrack.track.trackId;
      return {
        trackType,
        track: item.filteredTrack.track,
        inputValue: item.checkedTrackIds.indexOf(item.filteredTrack.track.trackId) >= 0,
        selected,
        editing: selected && item.editingTrack,
        color: typeStylingRef.value.color(trackType),
        types: item.allTypes,
      };
    }

    watch(selectedTrackIdRef, scrollToTrack);
    watch(filteredTracksRef, scrollToSelectedTrack);


    async function multiDelete() {
      const tracksDisplayed: number[] = [];
      const text = ['Do you want to delete the following tracks:'];
      let count = 0;
      const limit = 20;
      virtualListItems.value.forEach((item) => {
        if (item.checkedTrackIds.includes(item.filteredTrack.track.trackId)) {
          if (count < limit) {
            text.push(item.filteredTrack.track.trackId.toString());
          }
          tracksDisplayed.push(item.filteredTrack.track.trackId);
          count += 1;
        }
      });
      if (count >= limit) {
        text.push(`And ${count - limit} more tracks...`);
      }

      const result = await prompt({
        title: 'Confirm',
        text,
        confirm: true,
      });
      if (result) {
        removeTrack(tracksDisplayed, true);
      }
    }

    const mouseTrap = computed(() => {
      const disabled = props.hotkeysDisabled;
      return [
        {
          bind: 'up',
          handler: (el: HTMLElement, event: KeyboardEvent) => {
            scrollPreventDefault(el, event, 'up');
          },
          disabled,
        },
        {
          bind: 'down',
          handler: (el: HTMLElement, event: KeyboardEvent) => {
            scrollPreventDefault(el, event, 'down');
          },
          disabled,
        },
        {
          bind: 'del',
          handler: () => {
            if (selectedTrackIdRef.value !== null) {
              removeTrack([selectedTrackIdRef.value]);
            }
          },
          disabled,
        },
        {
          bind: 'x',
          handler: () => trackSplit(selectedTrackIdRef.value, frameRef.value),
          disabled,
        },
      ];
    });

    const virtualHeight = computed(() => props.height - TrackListHeaderHeight);

    return {
      allTypes: allTypesRef,
      data,
      getItemProps,
      mouseTrap,
      newTrackColor,
      filteredTracks: filteredTracksRef,
      trackAdd,
      virtualHeight,
      virtualListItems,
      virtualList,
      multiDelete,
    };
  },
});
</script>

<template>
  <div class="d-flex flex-column">
    <v-subheader class="flex-grow-1 trackHeader px-2">
      <v-container class="py-2">
        <v-row align="center">
          Tracks ({{ filteredTracks.length }})
          <v-spacer />
          <v-menu
            v-model="data.settingsActive"
            :close-on-content-click="false"
            :nudge-bottom="28"
          >
            <template #activator="{ on, attrs }">
              <v-btn
                icon
                small
                class="mr-2"
                v-bind="attrs"
                v-on="on"
              >
                <v-icon
                  small
                  :color="data.settingsActive ? 'accent' : 'default'"
                >
                  mdi-cog
                </v-icon>
              </v-btn>
            </template>
            <slot
              v-if="data.settingsActive"
              name="settings"
            />
          </v-menu>
          <v-tooltip
            open-delay="100"
            bottom
          >
            <template #activator="{ on }">
              <v-btn
                :disabled="filteredTracks.length === 0"
                icon
                small
                class="mr-2"
                v-on="on"
                @click="multiDelete()"
              >
                <v-icon
                  small
                  color="error"
                >
                  mdi-delete
                </v-icon>
              </v-btn>
            </template>
            <span>Delete visible items</span>
          </v-tooltip>
          <v-tooltip
            open-delay="200"
            bottom
            max-width="200"
          >
            <template #activator="{ on }">
              <v-btn
                outlined
                x-small
                class="mr-2"
                :color="newTrackColor"
                v-on="on"
                @click="trackAdd"
              >
                <v-icon small>
                  mdi-plus
                </v-icon>
                {{ newTrackMode }}
              </v-btn>
            </template>
            <span>Default Type: {{ newTrackType }}</span>
          </v-tooltip>
        </v-row>
      </v-container>
    </v-subheader>
    <datalist id="allTypesOptions">
      <option
        v-for="type in allTypes"
        :key="type"
        :value="type"
      >
        {{ type }}
      </option>
    </datalist>
    <v-virtual-scroll
      ref="virtualList"
      v-mousetrap="mouseTrap"
      class="tracks"
      :items="virtualListItems"
      :item-height="data.itemHeight"
      :height="virtualHeight"
      bench="1"
    >
      <template #default="{ item }">
        <track-item
          v-bind="getItemProps(item)"
          :lock-types="lockTypes"
          @seek="$emit('track-seek', $event)"
        />
      </template>
    </v-virtual-scroll>
  </div>
</template>

<style lang="scss">
.strcoller {
  height: 100%;
}
.trackHeader{
  height: auto;
}
.tracks {
  overflow-y: auto;
  overflow-x: hidden;

  .v-input--checkbox {
    label {
      white-space: pre-wrap;
    }
  }
}
</style>
