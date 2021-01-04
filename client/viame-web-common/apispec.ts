import { provide } from '@vue/composition-api';

import { use } from 'vue-media-annotator/provides';
import { TrackData, TrackId } from 'vue-media-annotator/track';
import { CustomStyle } from 'vue-media-annotator/use/useStyling';

type DatasetType = 'image-sequence' | 'video';
type MultiTrackRecord = Record<string, TrackData>;

interface Attribute {
  belongs: 'track' | 'detection';
  datatype: 'text' | 'number' | 'boolean';
  values?: string[];
  name: string;
  _id: string;
}

interface Pipe {
  name: string;
  pipe: string;
  type: string;
}

interface Category {
  description: string;
  pipes: Pipe[];
}

interface TrainingConfigs {
  configs: string[];
  default: string;
}

type Pipelines = Record<string, Category>;

interface SaveDetectionsArgs {
  delete: TrackId[];
  upsert: TrackData[];
}

interface FrameImage {
  url: string;
  filename: string;
}

/**
 * The parts of metadata a user should be able to modify.
 */
interface DatasetMetaMutable {
  customTypeStyling?: Record<string, CustomStyle>;
  confidenceFilters?: Record<string, number>;
}

interface DatasetMeta extends DatasetMetaMutable {
  imageData: FrameImage[];
  videoUrl: string | undefined;
  type: Readonly<DatasetType>;
  fps: Readonly<number | string>; // this will become mutable in the future.
}

interface Api {
  /**
   * @deprecated soon attributes will come from loadMetadata()
   */
  getAttributes(): Promise<Attribute[]>;
  setAttribute({ addNew, data }: {addNew: boolean | undefined; data: Attribute}): Promise<unknown>;
  deleteAttribute(data: Attribute): Promise<unknown>;

  getPipelineList(): Promise<Pipelines>;
  runPipeline(itemId: string, pipeline: Pipe): Promise<unknown>;

  getTrainingConfigurations(): Promise<TrainingConfigs>;
  runTraining(folderIds: string[], pipelineName: string, config: string): Promise<unknown>;

  loadMetadata(datasetId: string): Promise<DatasetMeta>;
  loadDetections(datasetId: string): Promise<MultiTrackRecord>;

  saveDetections(datasetId: string, args: SaveDetectionsArgs): Promise<unknown>;
  saveMetadata(datasetId: string, metadata: DatasetMetaMutable): Promise<unknown>;
}

const ApiSymbol = Symbol('api');

/**
 * provideApi specifies an implementation of the data persistence interface
 * for use in vue-web-common
 * @param api an api implementation
 */
function provideApi(api: Api) {
  provide(ApiSymbol, api);
}

function useApi() {
  return use<Readonly<Api>>(ApiSymbol);
}

export {
  provideApi,
  useApi,
};

export type {
  Api,
  Attribute,
  DatasetMeta,
  DatasetMetaMutable,
  DatasetType,
  FrameImage,
  MultiTrackRecord,
  Pipe,
  Pipelines,
  SaveDetectionsArgs,
  TrainingConfigs,
};
