export const POLICY_MAJOR_VERSION = '1';

export const POLICY_LINKS = {
  youtubeTerms: 'https://developers.google.com/youtube/terms/developer-policies',
  youtubePrivacy: 'https://policies.google.com/privacy',
  diopsideTerms: 'https://diopside.local/terms',
  diopsidePrivacy: 'https://diopside.local/privacy',
  youtubeDerived: 'https://developers.google.com/youtube/terms/derived-metrics-policy',
};

export interface PolicyRequirement {
  youtubeTerms: string;
  youtubePrivacy: string;
  diopsideTerms: string;
  diopsidePrivacy: string;
  derivedMetrics: string;
}

export const policyRequirements: PolicyRequirement = {
  youtubeTerms: POLICY_LINKS.youtubeTerms,
  youtubePrivacy: POLICY_LINKS.youtubePrivacy,
  diopsideTerms: POLICY_LINKS.diopsideTerms,
  diopsidePrivacy: POLICY_LINKS.diopsidePrivacy,
  derivedMetrics: POLICY_LINKS.youtubeDerived,
};
