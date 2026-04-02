import claimSchema from "../../../../../packages/contracts/schemas/claim.json";

export const claimContract = claimSchema;
export type ClaimStatus =
  (typeof claimSchema.properties.status.enum)[number];
