type TenantLike = {
  tenantKey: string;
};

const DEFAULT_TENANT_BY_CLOUD: Record<string, string> = {
  aws: "default",
  azure: "mg-algar-finops",
  oci: "OCI-TENANT-OCVS",
};

export function getDefaultTenantForCloud(cloud: string): string {
  return DEFAULT_TENANT_BY_CLOUD[cloud] ?? "";
}

export function resolveTenantForCloud(cloud: string, tenantOptions: TenantLike[], currentTenant: string): string {
  if (cloud === "all") {
    return "";
  }

  const hasTenant = (candidate: string) =>
    Boolean(candidate) && tenantOptions.some((tenant) => tenant.tenantKey === candidate);

  if (hasTenant(currentTenant)) {
    return currentTenant;
  }

  const preferredTenant = getDefaultTenantForCloud(cloud);
  if (hasTenant(preferredTenant)) {
    return preferredTenant;
  }
  if (tenantOptions.length > 0) {
    return tenantOptions[0]?.tenantKey ?? "";
  }
  return preferredTenant;
}
