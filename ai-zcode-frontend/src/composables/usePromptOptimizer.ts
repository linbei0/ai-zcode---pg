import { computed, ref, watch, type Ref } from 'vue'
import { message } from 'ant-design-vue'
import { optimizeAppPrompt } from '@/api/appController'

interface PromptSnapshot {
  before: string
  after: string
}

interface UsePromptOptimizerOptions {
  scene: API.PromptOptimizeScene
  getAppId?: () => number | undefined
}

export function usePromptOptimizer(
  promptRef: Ref<string>,
  options: UsePromptOptimizerOptions
) {
  const isOptimizing = ref(false)
  const snapshot = ref<PromptSnapshot | null>(null)
  const isInternalChange = ref(false)

  const canUndo = computed(() => {
    return !!snapshot.value && promptRef.value === snapshot.value.after
  })

  watch(
    promptRef,
    (value) => {
      if (isInternalChange.value) {
        isInternalChange.value = false
        return
      }
      if (snapshot.value && value !== snapshot.value.after) {
        snapshot.value = null
      }
    },
    { flush: 'sync' }
  )

  const clearOptimizationState = () => {
    snapshot.value = null
  }

  const applyPromptValue = (value: string) => {
    isInternalChange.value = true
    promptRef.value = value
  }

  const optimizePrompt = async () => {
    const trimmedPrompt = promptRef.value.trim()
    if (!trimmedPrompt || isOptimizing.value) {
      return false
    }

    isOptimizing.value = true
    try {
      const res = await optimizeAppPrompt({
        prompt: trimmedPrompt,
        scene: options.scene,
        appId: options.getAppId?.(),
      })

      if (res.data.code !== 0 || !res.data.data?.optimizedPrompt) {
        message.error(res.data.message || '提示词优化失败，请稍后重试')
        return false
      }

      const optimizedPrompt = res.data.data.optimizedPrompt.trim()
      if (!optimizedPrompt) {
        message.error('优化结果为空，请稍后重试')
        return false
      }

      snapshot.value = {
        before: promptRef.value,
        after: optimizedPrompt,
      }
      applyPromptValue(optimizedPrompt)
      message.success(res.data.data.mode === 'detail' ? '已深度优化提示词' : '已优化提示词')
      return true
    } catch (error) {
      console.error('优化提示词失败：', error)
      message.error('优化失败，请稍后重试')
      return false
    } finally {
      isOptimizing.value = false
    }
  }

  const undoOptimization = () => {
    if (!snapshot.value) {
      return
    }
    applyPromptValue(snapshot.value.before)
    snapshot.value = null
    message.success('已回退到优化前的提示词')
  }

  return {
    isOptimizing,
    canUndo,
    optimizePrompt,
    undoOptimization,
    clearOptimizationState,
  }
}
