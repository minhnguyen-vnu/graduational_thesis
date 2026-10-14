# Các operation cần phân xử

## S319-N0051  POST /groups
desc: Create Group | Create Group
- body:admin_ids string
- body:name string
- body:notes string
- body:user_ids string

Phương án:
- X: T=1; victim=body:admin_ids; role=-; order=-
- Y: T=1; victim=body:admin_ids; role=body:admin_ids; order=-

## S330-N0048  PUT /api/v1/orgs/{org_id}/admins/{admin_id}
desc: updateOrgAdmin | Invite Org Admin
schema: admin
- path:org_id string
- path:admin_id string
- body:admin_id string
- body:email string
- body:enable_two_factor boolean
- body:first_name string
- body:hours integer
- body:last_name string
- body:oauth_google boolean
- body:phone string
- body:phone2 string
- body:privileges array<object>
- body:privileges[].for_site boolean
- body:privileges[].msp_id string
- body:privileges[].msp_logo_url string
- body:privileges[].msp_name string
- body:privileges[].msp_url string
- body:privileges[].name string
- body:privileges[].org_id string
- body:privileges[].org_name string
- body:privileges[].orggroup_ids array<string>
- body:privileges[].role string enum[admin|write|read|helpdesk|installer]
- body:privileges[].scope string enum[org|site|msp|orggroup]
- body:privileges[].site_id string
- body:privileges[].sitegroup_ids array<string>
- body:privileges[].views array<string>
- body:session_expiry integer
- body:tags array<string>
- body:two_factor_verified boolean
- body:via_sso string

Phương án:
- X: T=1; victim=path:admin_id; role=body:privileges; order=unordered
- Y: T=1; victim=path:admin_id; role=body:privileges; order=read<helpdesk<installer<write<admin
- Z: T=1; victim=body:admin_id|path:admin_id; role=body:privileges; order=-

## S330-N0227  PUT /api/v1/self
desc: updateSelf | update Account Information
schema: admin
- body:admin_id string
- body:email string
- body:enable_two_factor boolean
- body:first_name string
- body:hours integer
- body:last_name string
- body:oauth_google boolean
- body:phone string
- body:phone2 string
- body:privileges array<object>
- body:privileges[].for_site boolean
- body:privileges[].msp_id string
- body:privileges[].msp_logo_url string
- body:privileges[].msp_name string
- body:privileges[].msp_url string
- body:privileges[].name string
- body:privileges[].org_id string
- body:privileges[].org_name string
- body:privileges[].orggroup_ids array<string>
- body:privileges[].role string enum[admin|write|read|helpdesk|installer]
- body:privileges[].scope string enum[org|site|msp|orggroup]
- body:privileges[].site_id string
- body:privileges[].sitegroup_ids array<string>
- body:privileges[].views array<string>
- body:session_expiry integer
- body:tags array<string>
- body:two_factor_verified boolean
- body:via_sso string

Phương án:
- X: T=1; victim=self; role=body:privileges; order=unordered
- Y: T=1; victim=self; role=body:privileges; order=installer<read<helpdesk<write<admin
- Z: T=1; victim=self; role=body:privileges; order=read<helpdesk<installer<write<admin

