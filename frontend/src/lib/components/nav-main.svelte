<script lang="ts">
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  let {
    items,
  }: {
    items: {
      title: string;
      url: string;
      // This should be `Component` after @lucide/svelte updates types
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      icon: any;
      isActive?: boolean;
      items?: {
        title: string;
        url: string;
      }[];
    }[];
  } = $props();
</script>
<Sidebar.Group>
  <Sidebar.GroupLabel>Platform</Sidebar.GroupLabel>
  <Sidebar.Menu>
    {#each items as mainItem (mainItem.title)}
      <Sidebar.MenuItem>
        <Sidebar.MenuButton tooltipContent={mainItem.title}>
          {#snippet child({ props })}
            <a href={mainItem.url} {...props}>
              <mainItem.icon />
              <span>{mainItem.title}</span>
            </a>
          {/snippet}
        </Sidebar.MenuButton>
        {#if mainItem.items?.length}
          <Sidebar.MenuSub>
            {#each mainItem.items as subItem (subItem.title)}
              <Sidebar.MenuSubItem>
                <Sidebar.MenuSubButton href={subItem.url}>
                  <span>{subItem.title}</span>
                </Sidebar.MenuSubButton>
              </Sidebar.MenuSubItem>
            {/each}
          </Sidebar.MenuSub>
        {/if}
      </Sidebar.MenuItem>
    {/each}
  </Sidebar.Menu>
</Sidebar.Group>