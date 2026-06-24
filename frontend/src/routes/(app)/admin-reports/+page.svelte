<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import * as Table from '$lib/components/ui/table';
  import { Spinner } from '$lib/components/ui/loading';
  import Download from '@lucide/svelte/icons/download';
  import Search from '@lucide/svelte/icons/search';
  import { openProtectedMedia } from '$lib/utils/mediaAccess';
  import {
    downloadReportExcel,
    fetchAdminReportMeta,
    fetchReportData,
    type AdminReportMeta,
    type ReportDefinition,
    type ReportFilters,
  } from '$lib/api/adminReports';

  let loading = $state(true);
  let exporting = $state(false);
  let error = $state('');
  let meta = $state<AdminReportMeta | null>(null);
  let activeSlug = $state('chat_activity');
  let reportData = $state<Record<string, unknown>[]>([]);
  let breakdownData = $state<Record<string, unknown>[]>([]);
  let detailsData = $state<Record<string, unknown>[]>([]);
  let count = $state(0);
  let page = $state(1);
  let pageSize = $state(25);

  let fromDate = $state('');
  let toDate = $state('');
  let status = $state('');
  let category = $state('');
  let rating = $state('');
  let searchQuery = $state('');

  const paginatedReports = new Set(['form_feedback', 'response_feedback']);
  const totalPages = $derived(Math.max(1, Math.ceil(count / pageSize)));

  const activeReport = $derived(
    meta?.reports.find((report) => report.slug === activeSlug) ?? null
  );

  const groupedReports = $derived.by(() => {
    const groups = new Map<string, ReportDefinition[]>();
    for (const report of meta?.reports ?? []) {
      const items = groups.get(report.category) ?? [];
      items.push(report);
      groups.set(report.category, items);
    }
    return [...groups.entries()];
  });

  function currentFilters(): ReportFilters {
    const filters: ReportFilters = {
      from_date: fromDate || undefined,
      to_date: toDate || undefined,
      category: category || undefined,
      q: searchQuery || undefined,
    };
    if (activeSlug === 'form_feedback') {
      filters.status = status || undefined;
    }
    if (activeSlug === 'response_feedback') {
      filters.rating = rating || undefined;
    }
    if (paginatedReports.has(activeSlug)) {
      filters.page = page;
      filters.page_size = pageSize;
    }
    return filters;
  }

  function formatDate(value: unknown) {
    if (!value || typeof value !== 'string') return '—';
    return new Date(value).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function truncate(text: unknown, max = 100) {
    if (!text || typeof text !== 'string') return '';
    return text.length > max ? `${text.slice(0, max)}...` : text;
  }

  function boolLabel(value: unknown) {
    return value ? 'Yes' : 'No';
  }

  async function loadReport() {
    loading = true;
    error = '';
    reportData = [];
    breakdownData = [];
    detailsData = [];
    try {
      const data = await fetchReportData<Record<string, unknown>>(activeSlug, currentFilters());
      if (activeSlug === 'negative_feedback') {
        breakdownData = data.breakdown ?? [];
        detailsData = data.details ?? [];
        count = data.count ?? detailsData.length;
      } else {
        reportData = data.results ?? [];
        count = data.count ?? reportData.length;
        if (data.page) page = data.page;
        if (data.page_size) pageSize = data.page_size;
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load report';
      toast.error(error);
    } finally {
      loading = false;
    }
  }

  async function handleExport(all = false) {
    exporting = true;
    try {
      await downloadReportExcel(all ? null : activeSlug, currentFilters());
      if (all) {
        toast.success('All reports downloaded — open the Index tab, then switch sheets at the bottom');
      } else {
        toast.success(`${activeReport?.name ?? 'Report'} downloaded with full row details`);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to export report');
    } finally {
      exporting = false;
    }
  }

  function selectReport(slug: string) {
    activeSlug = slug;
    page = 1;
    status = '';
    rating = '';
    category = '';
    loadReport();
  }

  function applyFilters() {
    page = 1;
    loadReport();
  }

  function goToPage(nextPage: number) {
    page = nextPage;
    loadReport();
  }

  onMount(async () => {
    try {
      meta = await fetchAdminReportMeta();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load report catalog');
    }
    await loadReport();
  });
</script>

<svelte:head>
  <title>Admin Reports - MoSPI StatsDoc</title>
</svelte:head>

<AuthGuard requireAdmin={true}>
  <div class="w-full h-full overflow-auto p-6 space-y-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Admin Reports</h1>
        <p class="text-sm text-muted-foreground mt-1">
          Select a report from the left panel. Use <strong>Download This Report</strong> for one Excel file with full row details.
          Use <strong>Download All</strong> for a multi-tab workbook (see the Index tab for sheet names).
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button variant="outline" onclick={() => handleExport(false)} disabled={exporting || loading}>
          {#if exporting}
            <Spinner class="size-4 mr-2" />
          {:else}
            <Download class="size-4 mr-2" />
          {/if}
          Download: {activeReport?.name ?? 'Report'}
        </Button>
        <Button onclick={() => handleExport(true)} disabled={exporting || loading}>
          {#if exporting}
            <Spinner class="size-4 mr-2" />
          {:else}
            <Download class="size-4 mr-2" />
          {/if}
          Download All (15 sheets)
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[280px_1fr] gap-6">
      <aside class="space-y-4">
        {#each groupedReports as [categoryName, reports]}
          <div class="rounded-lg border bg-white dark:bg-gray-900 p-3">
            <h2 class="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
              {categoryName}
            </h2>
            <div class="space-y-1">
              {#each reports as report}
                <button
                  type="button"
                  class="w-full text-left rounded-md px-3 py-2 text-sm transition-colors {activeSlug === report.slug ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}"
                  onclick={() => selectReport(report.slug)}
                >
                  <div class="font-medium">{report.name}</div>
                  <div class="text-xs opacity-80 mt-0.5">{report.description}</div>
                </button>
              {/each}
            </div>
          </div>
        {/each}
      </aside>

      <section class="space-y-4">
        {#if activeReport}
          <div class="rounded-lg border bg-white dark:bg-gray-900 p-4">
            <div class="flex items-center gap-2">
              <h2 class="text-xl font-semibold">{activeReport.name}</h2>
              <Badge variant="outline">Phase {activeReport.phase}</Badge>
            </div>
            <p class="text-sm text-muted-foreground mt-1">{activeReport.description}</p>
          </div>
        {/if}

        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 p-4 border rounded-lg bg-white dark:bg-gray-900">
          <div class="space-y-2">
            <Label for="from-date">From date</Label>
            <Input id="from-date" type="date" bind:value={fromDate} />
          </div>
          <div class="space-y-2">
            <Label for="to-date">To date</Label>
            <Input id="to-date" type="date" bind:value={toDate} />
          </div>

          {#if activeSlug === 'form_feedback'}
            <div class="space-y-2">
              <Label for="status">Status</Label>
              <select id="status" bind:value={status} class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="">All statuses</option>
                {#each meta?.form_statuses || [] as option}
                  <option value={option.value}>{option.label}</option>
                {/each}
              </select>
            </div>
          {:else if activeSlug === 'response_feedback'}
            <div class="space-y-2">
              <Label for="rating">Rating</Label>
              <select id="rating" bind:value={rating} class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="">All ratings</option>
                {#each meta?.response_ratings || [] as option}
                  <option value={option.value}>{option.label}</option>
                {/each}
              </select>
            </div>
          {/if}

          {#if ['form_feedback', 'response_feedback', 'citation_accuracy', 'language_issues', 'negative_feedback'].includes(activeSlug)}
            <div class="space-y-2 xl:col-span-2">
              <Label for="search">Search</Label>
              <div class="flex gap-2">
                <Input
                  id="search"
                  placeholder="Search report data..."
                  bind:value={searchQuery}
                  onkeydown={(event) => event.key === 'Enter' && applyFilters()}
                />
                <Button onclick={applyFilters}>
                  <Search class="size-4" />
                </Button>
              </div>
            </div>
          {:else}
            <div class="flex items-end">
              <Button onclick={applyFilters} class="w-full">
                <Search class="size-4 mr-2" />
                Apply Filters
              </Button>
            </div>
          {/if}
        </div>

        {#if loading}
          <div class="flex items-center justify-center py-16">
            <Spinner class="size-8" />
          </div>
        {:else if error}
          <div class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        {:else if activeSlug === 'negative_feedback'}
          <div class="space-y-6">
            <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
              <div class="px-4 py-3 border-b font-medium">Breakdown by reason</div>
              <Table.Root>
                <Table.Header>
                  <Table.Row>
                    <Table.Head>Category</Table.Head>
                    <Table.Head>Label</Table.Head>
                    <Table.Head>Count</Table.Head>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {#if breakdownData.length === 0}
                    <Table.Row>
                      <Table.Cell colspan={3} class="text-center text-muted-foreground py-8">No negative feedback found.</Table.Cell>
                    </Table.Row>
                  {:else}
                    {#each breakdownData as row}
                      <Table.Row>
                        <Table.Cell>{row.category}</Table.Cell>
                        <Table.Cell>{row.category_label}</Table.Cell>
                        <Table.Cell>{row.count}</Table.Cell>
                      </Table.Row>
                    {/each}
                  {/if}
                </Table.Body>
              </Table.Root>
            </div>

            <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
              <div class="px-4 py-3 border-b font-medium">Recent negative feedback</div>
              <Table.Root>
                <Table.Header>
                  <Table.Row>
                    <Table.Head>User</Table.Head>
                    <Table.Head>Category</Table.Head>
                    <Table.Head>Details</Table.Head>
                    <Table.Head>Question</Table.Head>
                    <Table.Head>Submitted</Table.Head>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {#if detailsData.length === 0}
                    <Table.Row>
                      <Table.Cell colspan={5} class="text-center text-muted-foreground py-8">No details found.</Table.Cell>
                    </Table.Row>
                  {:else}
                    {#each detailsData as row}
                      <Table.Row>
                        <Table.Cell>{row.user_email}</Table.Cell>
                        <Table.Cell>{row.category_label}</Table.Cell>
                        <Table.Cell>{truncate(row.details, 80)}</Table.Cell>
                        <Table.Cell>{truncate(row.user_question, 80)}</Table.Cell>
                        <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.created_at)}</Table.Cell>
                      </Table.Row>
                    {/each}
                  {/if}
                </Table.Body>
              </Table.Root>
            </div>
          </div>
        {:else if activeSlug === 'form_feedback'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>Name</Table.Head>
                  <Table.Head>Email</Table.Head>
                  <Table.Head>Subject</Table.Head>
                  <Table.Head>Attachments</Table.Head>
                  <Table.Head>Status</Table.Head>
                  <Table.Head>Submitted</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#if reportData.length === 0}
                  <Table.Row>
                    <Table.Cell colspan={6} class="text-center text-muted-foreground py-8">No records found.</Table.Cell>
                  </Table.Row>
                {:else}
                  {#each reportData as row}
                    <Table.Row>
                      <Table.Cell class="font-medium">{row.name}</Table.Cell>
                      <Table.Cell>{row.email}</Table.Cell>
                      <Table.Cell>{truncate(row.subject, 80)}</Table.Cell>
                      <Table.Cell>
                        {#if row.attachments?.length}
                          <div class="flex flex-col gap-1">
                            {#each row.attachments as attachment}
                              <button
                                type="button"
                                class="text-sm text-blue-600 hover:underline dark:text-blue-400 text-left"
                                onclick={() => openProtectedMedia(attachment.url)}
                              >
                                {attachment.original_filename}
                              </button>
                            {/each}
                          </div>
                        {:else}
                          <span class="text-muted-foreground">—</span>
                        {/if}
                      </Table.Cell>
                      <Table.Cell><Badge variant="outline">{row.status}</Badge></Table.Cell>
                      <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.created_at)}</Table.Cell>
                    </Table.Row>
                  {/each}
                {/if}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'response_feedback'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>User</Table.Head>
                  <Table.Head>Rating</Table.Head>
                  <Table.Head>Category</Table.Head>
                  <Table.Head>Question</Table.Head>
                  <Table.Head>Submitted</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#if reportData.length === 0}
                  <Table.Row>
                    <Table.Cell colspan={5} class="text-center text-muted-foreground py-8">No records found.</Table.Cell>
                  </Table.Row>
                {:else}
                  {#each reportData as row}
                    <Table.Row>
                      <Table.Cell>{row.user_email || row.user_username}</Table.Cell>
                      <Table.Cell>
                        <Badge variant={row.rating === 'up' ? 'default' : 'destructive'}>
                          {row.rating === 'up' ? 'Helpful' : 'Not helpful'}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell>{row.category_label || '—'}</Table.Cell>
                      <Table.Cell>{truncate(row.user_question, 80)}</Table.Cell>
                      <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.created_at)}</Table.Cell>
                    </Table.Row>
                  {/each}
                {/if}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'chat_activity'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>Date</Table.Head>
                  <Table.Head>Chats</Table.Head>
                  <Table.Head>Active Users</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell>{row.date}</Table.Cell>
                    <Table.Cell>{row.chat_count}</Table.Cell>
                    <Table.Cell>{row.active_users}</Table.Cell>
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={3} class="text-center text-muted-foreground py-8">No chat activity found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'kb_usage'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>Knowledge Base</Table.Head>
                  <Table.Head>Chats</Table.Head>
                  <Table.Head>Files</Table.Head>
                  <Table.Head>Completed</Table.Head>
                  <Table.Head>Failed</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell class="font-medium">{row.name}</Table.Cell>
                    <Table.Cell>{row.chat_count}</Table.Cell>
                    <Table.Cell>{row.file_count}</Table.Cell>
                    <Table.Cell>{row.completed_files}</Table.Cell>
                    <Table.Cell>{row.failed_files}</Table.Cell>
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={5} class="text-center text-muted-foreground py-8">No knowledge bases found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'user_activity'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>User</Table.Head>
                  <Table.Head>Email</Table.Head>
                  <Table.Head>Chat Count</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell>{row.username}</Table.Cell>
                    <Table.Cell>{row.email}</Table.Cell>
                    <Table.Cell>{row.chat_count}</Table.Cell>
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={3} class="text-center text-muted-foreground py-8">No user activity found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'document_uploads'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>File</Table.Head>
                  <Table.Head>Status</Table.Head>
                  <Table.Head>Knowledge Base</Table.Head>
                  <Table.Head>Uploaded</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell class="font-medium">{row.file_name}</Table.Cell>
                    <Table.Cell><Badge variant="outline">{row.status}</Badge></Table.Cell>
                    <Table.Cell>{row.knowledge_base}</Table.Cell>
                    <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.uploaded_at)}</Table.Cell>
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={4} class="text-center text-muted-foreground py-8">No uploads found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'failed_uploads'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>File</Table.Head>
                  <Table.Head>Knowledge Base</Table.Head>
                  <Table.Head>Error</Table.Head>
                  <Table.Head>Uploaded</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell class="font-medium">{row.file_name}</Table.Cell>
                    <Table.Cell>{row.knowledge_base}</Table.Cell>
                    <Table.Cell>{truncate(row.error || row.technical_error, 120)}</Table.Cell>
                    <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.uploaded_at)}</Table.Cell>
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={4} class="text-center text-muted-foreground py-8">No failed uploads found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'user_list' || activeSlug === 'login_activity'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>Username</Table.Head>
                  <Table.Head>Email</Table.Head>
                  <Table.Head>Active</Table.Head>
                  <Table.Head>Staff</Table.Head>
                  <Table.Head>Last Login</Table.Head>
                  {#if activeSlug === 'login_activity'}
                    <Table.Head>Days Since Login</Table.Head>
                  {/if}
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell class="font-medium">{row.username}</Table.Cell>
                    <Table.Cell>{row.email}</Table.Cell>
                    <Table.Cell>{boolLabel(row.is_active)}</Table.Cell>
                    <Table.Cell>{boolLabel(row.is_staff)}</Table.Cell>
                    <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.last_login)}</Table.Cell>
                    {#if activeSlug === 'login_activity'}
                      <Table.Cell>{row.days_since_login === '' ? '—' : row.days_since_login}</Table.Cell>
                    {/if}
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={activeSlug === 'login_activity' ? 6 : 5} class="text-center text-muted-foreground py-8">No users found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'admin_audit_log'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>Time</Table.Head>
                  <Table.Head>Admin</Table.Head>
                  <Table.Head>Action</Table.Head>
                  <Table.Head>Object</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.action_time)}</Table.Cell>
                    <Table.Cell>{row.user}</Table.Cell>
                    <Table.Cell>{row.action}</Table.Cell>
                    <Table.Cell>{truncate(row.object_repr, 80)}</Table.Cell>
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={4} class="text-center text-muted-foreground py-8">No admin actions found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {:else if activeSlug === 'citation_accuracy' || activeSlug === 'language_issues'}
          <div class="rounded-lg border bg-white dark:bg-gray-900 overflow-hidden">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.Head>User</Table.Head>
                  <Table.Head>Details</Table.Head>
                  <Table.Head>Question</Table.Head>
                  <Table.Head>Response</Table.Head>
                  <Table.Head>Submitted</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {#each reportData as row}
                  <Table.Row>
                    <Table.Cell>{row.user_email}</Table.Cell>
                    <Table.Cell>{truncate(row.details, 80)}</Table.Cell>
                    <Table.Cell>{truncate(row.user_question, 80)}</Table.Cell>
                    <Table.Cell>{truncate(row.assistant_response, 80)}</Table.Cell>
                    <Table.Cell class="text-sm text-muted-foreground">{formatDate(row.created_at)}</Table.Cell>
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={5} class="text-center text-muted-foreground py-8">No records found.</Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
        {/if}

        {#if !loading && count > 0 && paginatedReports.has(activeSlug)}
          <div class="flex items-center justify-between">
            <p class="text-sm text-muted-foreground">
              Showing page {page} of {totalPages} ({count} total)
            </p>
            <div class="flex gap-2">
              <Button variant="outline" disabled={page <= 1} onclick={() => goToPage(page - 1)}>Previous</Button>
              <Button variant="outline" disabled={page >= totalPages} onclick={() => goToPage(page + 1)}>Next</Button>
            </div>
          </div>
        {:else if !loading && count > 0}
          <p class="text-sm text-muted-foreground">{count} record(s)</p>
        {/if}
      </section>
    </div>
  </div>
</AuthGuard>
