/**
 * React Query hook for item metadata suggestions.
 *
 * Manages:
 * - Loading state
 * - Error handling
 * - Retry logic
 * - Query caching
 */

import { useMutation, type UseMutationResult } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  suggestItemMetadata,
  generateItemAudio,
  searchItemImages,
  type SuggestItemMetadataRequest,
  type ItemMetadataSuggestion,
  type GenerateAudioRequest,
  type GenerateAudioResponse,
  type SearchImagesRequest,
  type ImageSuggestion,
} from '../api/item-suggestions.api';

/**
 * Hook to fetch item metadata suggestions.
 *
 * Usage:
 * ```tsx
 * const suggest = useSuggestItemMetadata();
 *
 * const handleSuggest = async () => {
 *   try {
 *     const suggestions = await suggest.mutateAsync({
 *       term: 'wanderlust',
 *       source_language: 'English',
 *       source_language_code: 'en-US',
 *     });
 *
 *     // Apply suggestions to form state
 *     setContext(suggestions.context);
 *     setPartOfSpeech(suggestions.part_of_speech);
 *     // ... etc
 *   } catch (error) {
 *     // Error already toasted by hook
 *   }
 * };
 * ```
 *
 * Error states:
 * - Network error → toast.error()
 * - API error → toast.error()
 * - Partial failure → suggestions with missing fields (nullable)
 */
export function useSuggestItemMetadata(): UseMutationResult<
  ItemMetadataSuggestion,
  Error,
  SuggestItemMetadataRequest
> {
  return useMutation({
    mutationFn: (request: SuggestItemMetadataRequest) =>
      suggestItemMetadata(request),
    retry: 1,
    retryDelay: 1000,
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to get suggestions');
    },
  });
}

export function useGenerateAudio(): UseMutationResult<
  GenerateAudioResponse,
  Error,
  GenerateAudioRequest
> {
  return useMutation({
    mutationFn: (request: GenerateAudioRequest) => generateItemAudio(request),
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to generate audio');
    },
  });
}

export function useSearchImages(): UseMutationResult<
  ImageSuggestion[],
  Error,
  SearchImagesRequest
> {
  return useMutation({
    mutationFn: (request: SearchImagesRequest) => searchItemImages(request),
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to fetch images');
    },
  });
}
