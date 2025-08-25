<script setup lang='ts'>
import {useRoute, useRouter} from 'vue-router'

import type { CSSProperties } from 'vue'
import { computed, ref, watch } from 'vue'
import { NButton, NLayoutSider } from 'naive-ui'
import List from './List.vue'
import Footer from './Footer.vue'
import { useAppStore, useChatStore } from '@/store'
import { useBasicLayout } from '@/hooks/useBasicLayout'
import { PromptStore } from '@/components/common'
import {router} from "@/router";
const appStore = useAppStore()
const chatStore = useChatStore()
const { isMobile } = useBasicLayout()
const show = ref(false)
const collapsed = computed(() => appStore.siderCollapsed)
const route = useRoute()
function handleAdd() {
	// 判断当前页面是否是 report
	if (route.name !== 'Report') {
		// 如果当前不是 report 页面，创建新的聊天记录
		chatStore.addHistory({ title: 'New Chat', uuid: Date.now(), isEdit: false })
		if (isMobile.value) {
			appStore.setSiderCollapsed(true)
		}
	} else {
		// 确保 historyList 是有效的数组
		const historyList = chatStore.history || [] // 如果是 undefined 或 null，则默认空数组

		// 如果 historyList 为空，创建一个新的历史记录
		if (historyList.length === 0) {
			const newHistory = { title: 'New Chat', uuid: Date.now(), isEdit: false }
			chatStore.addHistory(newHistory)  // 添加新的历史记录
			router.push({ name: 'Chat', params: { uuid: newHistory.uuid } }) // 跳转到新创建的聊天
		} else {
			// 获取最新的历史记录
			const latestHistory = historyList[historyList.length - 1]

			if (latestHistory) {
				router.push({ name: 'Chat', params: { uuid: latestHistory.uuid } }) // 跳转到该聊天
			} else {
				console.log('没有找到历史记录')  // Debug: 打印没有历史记录的情况
			}
		}
	}
}



function handleUpdateCollapsed() {
  appStore.setSiderCollapsed(!collapsed.value)
}
const getMobileClass = computed<CSSProperties>(() => {
  if (isMobile.value) {
    return {
      position: 'fixed',
      zIndex: 50,
    }
  }
  return {}
})
const mobileSafeArea = computed(() => {
  if (isMobile.value) {
    return {
      paddingBottom: 'env(safe-area-inset-bottom)',
    }
  }
  return {}
})

function handleGoToReport() {
	router.push({ name: 'Report' })
}


watch(
  isMobile,
  (val) => {
    appStore.setSiderCollapsed(val)
  },
  {
    immediate: true,
    flush: 'post',
  },
)
</script>

<template>
  <NLayoutSider
    :collapsed="collapsed"
    :collapsed-width="0"
    :width="260"
    :show-trigger="isMobile ? false : 'arrow-circle'"
    collapse-mode="transform"
    position="absolute"
    bordered
    :style="getMobileClass"
    @update-collapsed="handleUpdateCollapsed"
  >
    <div class="flex flex-col h-full" :style="mobileSafeArea">
      <main class="flex flex-col flex-1 min-h-0">
        <div class="p-4">
          <NButton dashed block @click="handleGoToReport">
            报告管理
					</NButton>
					<NButton dashed block @click="handleAdd">
						{{ $t('chat.newChatButton') }}
					</NButton>
        </div>
        <div class="flex-1 min-h-0 pb-4 overflow-hidden">
          <List />
        </div>
        <div class="p-4">

        </div>
      </main>
      <Footer />
    </div>
  </NLayoutSider>
  <template v-if="isMobile">
    <div v-show="!collapsed" class="fixed inset-0 z-40 bg-black/40" @click="handleUpdateCollapsed" />
  </template>
  <PromptStore v-model:visible="show" />
</template>
