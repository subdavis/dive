<script lang="ts">
import {
  computed, defineComponent, reactive, Ref,
} from '@vue/composition-api';
import { difference, union } from 'lodash';

import { usePrompt } from 'dive-common/vue-utilities/prompt-service';
import {
  useCheckedTypes, useAllTypes, useTypeStyling, useHandler,
  useUsedTypes, useFilteredTracks, useConfidenceFilters,
} from '../provides';
import TooltipBtn from './TooltipButton.vue';
import TypeEditor from './TypeEditor.vue';
import TypeItem from './TypeItem.vue';

interface VirtualTypeItem {
  type: string;
  confidenceFilterNum: number;
  displayText: string;
  color: string;
  checked: boolean;
}

/* Magic numbers involved in height calculation */
const TypeListHeaderHeight = 80;

export default defineComponent({
  name: 'TypeList',

  props: {
    showEmptyTypes: {
      type: Boolean,
      default: false,
    },
    height: {
      type: Number,
      default: 200,
    },
    width: {
      type: Number,
      default: 300,
    },
  },

  components: { TypeEditor, TooltipBtn, TypeItem },

  setup(props) {
    const { prompt } = usePrompt();

    // Ordering of these lists should match
    const sortingMethods = ['a-z', 'count'];
    const sortingMethodIcons = ['mdi-sort-alphabetical-ascending', 'mdi-sort-numeric-ascending'];

    const data = reactive({
      showPicker: false,
      selectedColor: '',
      selectedType: '',
      editingType: '',
      editingColor: '',
      editingThickness: 5,
      editingFill: false,
      editingOpacity: 1.0,
      valid: true,
      settingsActive: false,
      sortingMethod: 0, // index into sortingMethods
      filterText: '',
    });
    const checkedTypesRef = useCheckedTypes();
    const allTypesRef = useAllTypes();
    const usedTypesRef = useUsedTypes();
    const typeStylingRef = useTypeStyling();
    const filteredTracksRef = useFilteredTracks();
    const confidenceFiltersRef = useConfidenceFilters();
    const {
      setCheckedTypes,
      removeTypeTracks,
    } = useHandler();

    function clickEdit(type: string) {
      data.selectedType = type;
      data.editingType = data.selectedType;
      data.showPicker = true;
      data.editingColor = typeStylingRef.value.color(type);
      data.editingThickness = typeStylingRef.value.strokeWidth(type);
      data.editingFill = typeStylingRef.value.fill(type);
      data.editingOpacity = typeStylingRef.value.opacity(type);
    }

    function clickSortToggle() {
      data.sortingMethod = (data.sortingMethod + 1) % sortingMethods.length;
    }

    async function clickDelete() {
      const typeDisplay: string[] = [];
      const text = ['This will remove the type from any visible track or delete the track if it is the only type.',
        'Do you want to delete all tracks of following types:'];
      checkedTypesRef.value.forEach((item) => {
        typeDisplay.push(item);
        text.push(item.toString());
      });

      const result = await prompt({
        title: 'Confirm',
        text,
        confirm: true,
      });
      if (result) {
        removeTypeTracks([...checkedTypesRef.value]);
      }
    }

    const typeCounts = computed(() => filteredTracksRef.value.reduce((acc, filteredTrack) => {
      const confidencePair = filteredTrack.track.getType(filteredTrack.context.confidencePairIndex);
      const trackType = confidencePair[0];
      acc.set(trackType, (acc.get(trackType) || 0) + 1);

      return acc;
    }, new Map<string, number>()));

    function sortAndFilterTypes(types: Ref<readonly string[]>) {
      const filtered = types.value
        .filter((t) => t.toLowerCase().includes(data.filterText.toLowerCase()));
      switch (sortingMethods[data.sortingMethod]) {
        case 'a-z':
          return filtered.sort();
        case 'count':
          return filtered.sort(
            (a, b) => (typeCounts.value.get(b) || 0) - (typeCounts.value.get(a) || 0),
          );
        default:
          return filtered;
      }
    }

    const visibleTypes = computed(() => {
      if (props.showEmptyTypes) {
        return sortAndFilterTypes(allTypesRef);
      }
      return sortAndFilterTypes(usedTypesRef);
    });
    const virtualTypes: Ref<readonly VirtualTypeItem[]> = computed(() => {
      const confidenceFiltersDeRef = confidenceFiltersRef.value;
      const typeCountsDeRef = typeCounts.value;
      const typeStylingDeRef = typeStylingRef.value;
      const checkedTypesDeRef = checkedTypesRef.value;
      return visibleTypes.value.map((item) => ({
        type: item,
        confidenceFilterNum: confidenceFiltersDeRef[item] || 0,
        displayText: `${item} (${typeCountsDeRef.get(item) || 0})`,
        color: typeStylingDeRef.color(item),
        checked: checkedTypesDeRef.includes(item),
      }));
    });
    const headCheckState = computed(() => {
      const uncheckedTypes = difference(visibleTypes.value, checkedTypesRef.value);
      if (uncheckedTypes.length === 0) {
        return 1;
      } if (uncheckedTypes.length === visibleTypes.value.length) {
        return 0;
      }
      return -1;
    });

    function headCheckClicked() {
      if (headCheckState.value === 0) {
        /* Enable only what is filtered AND don't change what isn't filtered */
        const allVisibleAndCheckedInvisible = union(
          /* What was already checked and is currently not visible */
          difference(checkedTypesRef.value, visibleTypes.value),
          /* What is visible */
          visibleTypes.value,
        );
        setCheckedTypes(allVisibleAndCheckedInvisible);
      } else {
        /* Disable whatever is both checked and filtered */
        const invisible = difference(checkedTypesRef.value, visibleTypes.value);
        setCheckedTypes(invisible);
      }
    }


    function updateCheckedType(evt: boolean, type: string) {
      if (evt) {
        setCheckedTypes(checkedTypesRef.value.concat([type]));
      } else {
        setCheckedTypes(difference(checkedTypesRef.value, [type]));
      }
    }

    const virtualHeight = computed(() => props.height - TypeListHeaderHeight);

    return {
      data,
      headCheckState,
      visibleTypes,
      usedTypesRef,
      checkedTypesRef,
      confidenceFiltersRef,
      typeStylingRef,
      typeCounts,
      sortingMethods,
      sortingMethodIcons,
      virtualHeight,
      virtualTypes,
      /* methods */
      clickDelete,
      clickEdit,
      clickSortToggle,
      headCheckClicked,
      setCheckedTypes,
      updateCheckedType,
    };
  },
});
</script>

<template>
  <div class="d-flex flex-column">
    <v-container
      dense
      class="py-0"
    >
      <v-row
        class="border-highlight"
        align="center"
      >
        <v-col
          id="type-header"
          class="d-flex flex-row align-center py-0 mr-8"
        >
          <v-checkbox
            :input-value="headCheckState !== -1 ? headCheckState : false"
            :indeterminate="headCheckState === -1"
            dense
            shrink
            hide-details
            color="white"
            class="my-1 type-checkbox"
            @change="headCheckClicked"
          />
          <b>Type Filter</b>
          <v-spacer />
          <tooltip-btn
            :icon="sortingMethodIcons[data.sortingMethod]"
            tooltip-text="Sort types by count or alphabetically"
            @click="clickSortToggle"
          />
          <v-menu
            v-model="data.settingsActive"
            :nudge-bottom="28"
            :close-on-content-click="false"
          >
            <template #activator="{ on, attrs }">
              <v-btn
                icon
                small
                class="mx-2"
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
                class="hover-show-child"
                :disabled="checkedTypesRef.length === 0"
                icon
                small
                v-on="on"
                @click="clickDelete()"
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
        </v-col>
      </v-row>
    </v-container>
    <input
      id="search-types"
      v-model="data.filterText"
      type="text"
      placeholder="Search types"
      class="mx-2 mt-2 shrink input-box"
    >
    <div class="pb-2 overflow-y-hidden">
      <v-virtual-scroll
        class="tracks"
        :items="virtualTypes"
        :item-height="30"
        :height="virtualHeight"
        bench="1"
      >
        <template #default="{ item }">
          <type-item
            :type="item.type"
            :checked="item.checked"
            :color="item.color"
            :display-text="item.displayText"
            :confidence-filter-num="item.confidenceFilterNum"
            :width="width"
            @setCheckedTypes="updateCheckedType($event, item.type)"
            @clickEdit="clickEdit"
          />
        </template>
      </v-virtual-scroll>
    </div>
    <v-dialog
      v-model="data.showPicker"
      width="350"
    >
      <TypeEditor
        :selected-type="data.selectedType"
        @close="data.showPicker = false"
      />
    </v-dialog>
  </div>
</template>

<style scoped lang='scss'>
@import 'src/components/styles/common.scss';

.border-highlight {
   border-bottom: 1px solid gray;
 }

.type-checkbox {
  max-width: 80%;
  overflow-wrap: anywhere;
}

.hover-show-parent {
  .hover-show-child {
    display: none;
  }

  &:hover {
    .hover-show-child {
      display: inherit;
    }
  }
}
.outlined {
  background-color: gray;
  color: #222;
  font-weight: 600;
  border-radius: 6px;
  padding: 0 5px;
  font-size: 12px;
}
</style>
